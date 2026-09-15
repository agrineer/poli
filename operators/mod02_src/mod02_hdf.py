'''
@file mod02_hdf.py
@author Scott L. Williams
@package POLI
@brief Martial in MODIS mod02 hdf bands (1-index)
@LICENSE
#
#   Copyright (C) 2010-2025 Scott L. Williams
# 
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
'''
# embed copyright in binary
mod02_hdf_copyright = 'mod02_hdf.py Copyright (c) 2010-2025 Scott L. Williams released under GNU GPL V3.0'
# 
# martial in MODIS bands (1-index)
#
#        reflected       emitted      max resolution     notes  (dundee modis)
# band   range (uM)      range (uM)
#   1    0.620-0.670                       250m   Land / Cloud Boundaries red
#   2    0.841-0.876                       250m   Land / Cloud Boundaries
#   3    0.459-0.479                       500m   Land / Cloud Boundaries aqua
#   4    0.545-0.565                       500m   Land / Cloud Boundaries green
#   5    1.230-1.250                       500m   Land / Cloud Boundaries
#   6    1.628-1.652                       500m   Land / Cloud Boundaries
#   7    2.105-2.155                       500m   Land / Cloud Boundaries
#   8    0.405-0.420                        1km   Oc.Col/Phyplnk/Biogeoch violet
#   9    0.438-0.448                        1km   Oc.Col/Phyplnk/Biogeoch aqua
#  10    0.483-0.493                        1km   Oc.Col/Phyplnk/Biogeoch blue
#  11    0.526-0.536                        1km   Oc.Col/Phyplnk/Biogeoch green
#  12    0.546-0.556                        1km   Oc.Col/Phyplnk/Biogeoch green
#  13lo  0.662-0.672                        1km   Oc.Col/Phyplnk/Biogeoch red
#  13hi  0.662-0.672                        1km   Oc.Col/Phyplnk/Biogeoch red
#  14lo  0.673-0.683                        1km   Oc.Col/Phyplnk/Biogeoch red
#  14hi  0.673-0.683                        1km   Oc.Col/Phyplnk/Biogeoch red
#  15    0.743-0.753                        1km   Oc.Col/Phyplnk/Biogeoc
#  16    0.862-0.877                        1km   Oc.Col/Phyplnk/Biogeoc
#  17    0.890-0.920                        1km   Atmospheric Water Vapor
#  18    0.931-0.941                        1km   Atmospheric Water Vapro
#  19    0.915-0.965                        1km   Atmospheric Water Vapor
#  20                  3.660-3.840          1km   Surface / Cloud Temperature
#  21                  3.929-3.989          1km   Surface / Cloud Temperature sat. point=500 K
#  22                  3.929-3.989          1km   Surface / Cloud Temperature sat. point=335 K (less noisy)
#  23                  4.020-4.080          1km   Surface / Cloud Temperature
#  24                  4.433-4.498          1km   Atmospheric Temperature
#  25                  4.482-4.549          1km   Atmospheric Temperature
#  26    1.360-1.390                        1km   Cirrus Clouds Water Vapor
#  27                  6.535-6.895          1km   Cirrus Clouds Water Vapor
#  28                  7.175-7.475          1km   Cirrus Clouds Water Vapor
#  29                  8.400-8.700          1km   Cirrus Clouds Water Vapor
#  30                  9.580-9.880          1km   Ozone
#  31                 10.780-11.280         1km   Surface/Cloud Temperature
#  32                 11.770-12.270         1km   Surface/Cloud Temperature
#  33                 13.185-13.485         1km   Cloud Top Altitude
#  34                 13.485-13.785         1km   Cloud Top Altitude
#  35                 13.785-14.085         1km   Cloud Top Altitude
#  36                 14.085-14.385         1km   Cloud Top Altitude

import numpy as np
from ezprint import eprint

import scipy.ndimage as ndimage
from pyhdf.SD import SD, SDC, HDF4Error

class mod02_hdf():
    
    def __init__( self ):

        self.hdf_sd = None
        self.atype = None    # 250m,500m,1000m

        # band groupings (1-index) for 1km file
        self.EV_250_RefSB = ['1','2']
        
        self.EV_500_RefSB = ['3','4','5','6','7']
        
        self.EV_1KM_RefSB = ['8','9','10','11','12',
                             '13hi','13lo','14hi','14lo',
                             '15','16','17','18','19']
        
        self.EV_1KM_Emissive =['20','21','22','23','24',
                               '25','27','28','29','30',
                               '31','32','33','34','35','36']
        
    def open_file( self, filepath, mode='READ' ):   # open the hdf file

        if mode == 'CREATE':
            mode = SDC.WRITE|SDC.CREATE|SDC.TRUNC
            
        elif mode == 'WRITE':
            mode = SDC.WRITE
            
        elif mode == 'READ':
            mode = SDC.READ

        else:
            eprint( 'mod02_hdf: open_file: unknown mode:', mode,
                    ' returning' )
            return

        # string cast necessary for SD
        # when text is processed through textctrl FileDrop
        self.hdf_sd = SD( str(filepath), SDC.READ )

    def closefile( self ):
        
        self.hdf_sd.end()
        self.hsf_sd = None

    def getattr( self, name ):    # get single attribute by name

        if self.hdf_sd == None:
            eprint( 'mod02_hdf file not open' )
            return
        
        try:
            attr = self.hdf_sd.attr( name )  
            attr.index()            # gotta do this first
            return attr.get()

        except HDF4Error:
            return( 'mod02_hdf: getattr: attribute', name, 'unavailable' )
        
    def read_attributes( self ):    # read file attributes
        
        if self.hdf_sd == None:
            eprint( 'mod02_hdf: read_attributes: file not open' )
            return

        nscans = self.getattr( 'Number of Scans' )
        frames = self.getattr( 'Max Earth View Frames' )

        # determine resolution type by probing
        try:
            hdf = self.hdf_sd.select( 'EV_250_RefSB' )
            self.height = nscans*40
            self.width = frames*4
            self.atype = '250m'
        except:
            pass
        
        try:
            hdf = self.hdf_sd.select( 'EV_500_RefSB' )
            self.height = nscans*20
            self.width = frames*2
            self.atype = '500m'
        except:
            pass
        
        try:
            hdf = self.hdf_sd.select( 'EV_1KM_RefSB' )
            self.height = nscans*10
            self.width = frames
            self.atype = '1000m'
        except:
            pass

        if self.atype == None:
            eprint('mod02: read_attributes: cannot determine modis resolution')

    # return the data set attribute
    def getdata_attr( self, sd, name ):
        
        attr = sd.attr( name )
        attr.index()             
        return attr.get()
        
    def getband( self, dataset, index ):
        
        sd = self.hdf_sd.select( dataset )

        # get scale array and select ours
        scale_array = self.getdata_attr( sd, self.conv_scale )
        scale = scale_array[index]

        # get offset array and select ours
        offset_array = self.getdata_attr( sd, self.conv_offsets )
        offset = offset_array[index]

        valid_range = self.getdata_attr( sd, 'valid_range' )

        temp = sd.get()           # is there a way just to get one band?
        channel = temp[index,:,:].astype( np.float32 )

        # get NaN mask for input array (no Nan for integers)
        bool = channel < valid_range[0]
        bool |= channel > valid_range[1]

        spect = channel-offset    # use scale and offset from hdf
        spect = scale*spect       # to get calibrated radiance values

                                  # TODO:for reflective bands more precise
                                  # radiance values can be calculated
                                  # from reflectance values pg. 39
                                  # MODIS level 1b product users guide

        masked = np.ma.array( spect, mask=bool ) # replace with NaN
        return  masked.filled( np.nan )

    def EV_Band26( self ):
        sd = self.hdf_sd.select( 'EV_Band26' )
        scale  = self.getdata_attr( sd, self.conv_scale )
        offset = self.getdata_attr( sd, self.conv_offsets )
        valid_range = self.getdata_attr( sd, 'valid_range' )

        channel = sd.get()   
        tag = '1.360-1.390'

        # get NaN mask for input array (no Nan for integers)
        mbool = channel < valid_range[0]
        mbool |= channel > valid_range[1]

        spect = channel-offset       # use scale and offset from hdf
        spect = scale*spect          # to get calibrated values
        
        masked = np.ma.array( spect, mask=mbool ) # replace with NaN
        spect = masked.filled( np.nan )

        return spect, tag
 
    # TODO: make dictionaries unique and global

    def readband_1km( self, band ): # read a 1km spectral band

        # process according to band grouping
        if band in self.EV_250_RefSB:
            
            bufmap = {'1': 0, '2': 1 }
            tagmap = {'1': '0.620-0.670', '2':'0.841-0.876' }

            data = self.getband( 'EV_250_Aggr1km_RefSB', bufmap[band] )
            return data, tagmap[ band ]


        elif band in self.EV_500_RefSB:
            
            bufmap = {'3':0, '4':1, '5':2, '6':3, '7':4 }
            tagmap = {'3':'0.459-0.479', '4':'0.545-0.565',
                      '5':'1.230-1.250', '6':'1.628-1.652',
                      '7':'2.105-2.155' }

            data = self.getband( 'EV_500_Aggr1km_RefSB', bufmap[band] )
            return data, tagmap[ band ]

        elif band in self.EV_1KM_RefSB:
            
            bufmap = {'8':0, '9':1, '10':2, '11':3, '12':4,
                      '13lo':5, '13hi':6, '14lo':7, '14hi':8,
                      '15':9, '16':10,'17':11, '18':12, '19':13 }
            
            tagmap = {'8':'0.405-0.420', '9':'0.438-0.448', '10':'0.483-0.493',
                      '11':'0.526-0.536', '12':'0.546-0.556', 
                      '13lo':'0.662-0.672 lo', '13hi':'0.662-0.672 hi',
                      '14lo':'0.673-0.683 lo', '14hi':'0.673-0.683 hi',
                      '15':'0.743-0.753','16':'0.862-0.877','17':'0.890-0.920',
                      '18':'0.931-0.941', '19':'0.915-0.965' }

            data = self.getband( 'EV_1KM_RefSB', bufmap[band] )
            return data, tagmap[ band ]

        elif band in self.EV_1KM_Emissive:
            
            bufmap = {'20':0, '21':1, '22':2, '23':3, '24':4, '25':5,
                      '27':6, '28':7, '29':8, '30':9, '31':10, '32':11,
                      '33':12, '34':13, '35':14, '36':15 }
            
            tagmap = {'20':'3.660-3.840', '21':'3.929-3.989',
                      '22':'3.929-3.989??', '23':'4.020-4.080',
                      '24':'4.433-4.498', '24':'4.433-4.498',
                      '25':'4.482-4.549', '27':'6.535-6.895',
                      '28':'7.175-7.475', '29':'8.400-8.700',
                      '30':'9.580-9.880', '31':'10.780-11.280',
                      '32':'11.770-12.270', '33':'13.185-13.485',
                      '34':'13.485-13.785', '35':'13.785-14.085',
                      '36':'14.085-14.385' }

            data = self.getband('EV_1KM_Emissive', bufmap[band] )
            return data, tagmap[ band ]

        elif band == '26':    # special case (night active)
            return self.EV_Band26()
        
        else:
            eprint( 'band=', band, 'not recognized' )
            return None,None

    def readband_500m( self, band ): 

        # process according to band grouping
        
        if band in self.EV_250_RefSB:
            
            bufmap = {'1': 0, '2': 1 }
            tagmap = {'1': '0.620-0.670', '2':'0.841-0.876' }

            data = self.getband( 'EV_250_Aggr500_RefSB', bufmap[band] )
            return data, tagmap[ band ]

        elif band in self.EV_500_RefSB:
            
            bufmap = {'3':0, '4':1, '5':2, '6':3, '7':4 }
            tagmap = {'3':'0.459-0.479', '4':'0.545-0.565',
                      '5':'1.230-1.250', '6':'1.628-1.652',
                      '7':'2.105-2.155' }

            data = self.getband( 'EV_500_RefSB', bufmap[band] )
            return data, tagmap[ band ]

        else:
            eprint( 'mod02_src: readband_500m: band=', band, 'not recognized' )
            return None,None

    def readband_250m( self, band ):

        # process according to band grouping
        if band in self.EV_250_RefSB:
            
            bufmap = {'1': 0, '2': 1 }
            tagmap = {'1': '0.620-0.670', '2':'0.841-0.876' }

            data = self.getband( 'EV_250_RefSB', bufmap[band] )
            return data, tagmap[ band ]
        
        else:
            eprint( 'mod02_src: readband_250m: band=', band, 'not recognized' )
            return None,None

    # read a spectral band
    def readband( self, band, swconv='radiance' ):        

        # determine shortwave conversion type
        if band in self.EV_1KM_Emissive:      # overide for emmissive bands
            self.conv_scale = 'radiance_scales'
            self.conv_offsets = 'radiance_offsets'
            
        else:
            if swconv == 'radiance':
                self.conv_scale = 'radiance_scales'
                self.conv_offsets = 'radiance_offsets'
                eprint( 'mod0_hdf: radiance conversion on shortwave band=',
                        band )
                
            elif swconv == 'reflectance':
                self.conv_scale = 'reflectance_scales'
                self.conv_offsets = 'reflectance_offsets'
                eprint( 'mod02_hdf: reflectance conversion on shortwave band',
                        band )
            else:
                eprint( 'mod02_src: read_band: unknown conversion type:',
                        swconv )
                return None, None

        # determine resolution type
        if self.atype == '250m':
            return self.readband_250m( band )
        
        elif self.atype == '500m':
            return self.readband_500m( band )
        
        elif self.atype == '1000m':
            return self.readband_1km( band )

    def readangles( self, dataset ):
        
        sd = self.hdf_sd.select( dataset )

        valid_range = self.getdata_attr( sd, 'valid_range' )
        
        try:
            scale_factor = self.getdata_attr( sd, 'scale_factor' )
        except:
            scale_factor = 1.0

        try:
            add_offset = self.getdata_attr( sd, 'add_offset' );
        except:
            add_offset = 0.0

        # make output a float32; allows NaN implementation, 
        # whereas integer does not
        channel = np.empty( (self.height,self.width), dtype=np.float32)
        channel = sd.get()           # get data set
        height,width = channel.shape

        # angles are reduced resolution; interpolate
        zoom = ( self.height/float(height), self.width/float(width) )
        channel = ndimage.zoom( channel, zoom )
         
        # get NaN mask for input array (no Nan for integers)
        bool = channel < valid_range[0]
        bool |= channel > valid_range[1]

        channel = channel*scale_factor + add_offset
        masked = np.ma.array( channel, mask=bool ) # replace with NaN
        masked = masked.filled( np.nan )
        masked.shape = masked.shape[0], masked.shape[1], 1
        
        return masked
