#  ag_hdf.py
#

'''
@file ag_hdf.py
@author Scott L. Williams.
@package POLI
@brief  module to martial in AVHRR or GVISSR data 
@LICENSE

#  Copyright (C) 2010-2025 Scott L. Williams.
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
ag_hdf_copyright = 'ag_hdf.py Copyright (c) 2010-2025 Scott L. Williams ' + \
                   'released under GNU GPL V3.0'
# 
# martial in AVHRR or GVISSR data 
#
# AVHRR:
#   band  name         units    scale
#   0     avhrr_ch1    percent  0.01  00.58-00.68um at 1.1km
#   1     avhrr_ch2    percent  0.01  00.72-01.00um at 1.1km
#   2     avhrr_ch3    celsius  0.01  03.55-03.93um at 1.1km
#   3     avhrr_ch4    celsius  0.01  10.30-11.30um at 1.1km
#   4     avhrr_ch5    celsius  0.01  11.50-12.50um at 1.1km
#   5     avhrr_ch3a   percent  0.01  01.58-01.64um at 1.1km
#   6     latitude     degrees  0.01
#   7     longitude    degrees  0.01

#
# GVISSR:
#   band  name         units    scale
#   0     gvar_ch1     percent  0.01
#   1     gvar_ch2     celsius  0.01
#   2     gvar_ch3     celsius  0.01
#   3     gvar_ch4     celsius  0.01
#   4     gvar_ch5(6)  celsius  0.01     ( darn difference in11 and 12 )
#   5     latitude     degrees  0.01
#   6     longitude    degrees  0.01
#
# this class distinguishes between AVHRR and GVISSR files
# for op_panel labeling and navigational correction purposes
# GVAR GOES Var is the transmission protocol

import os
import sys
import numpy as np
from ezprint import eprint
from pyhdf.SD import HDF4Error

try:
    from ag_src.cwf_hdf import cwf_hdf  # GUI
except:
    from cwf_hdf import cwf_hdf         # non-GUI
    
class ag_hdf( cwf_hdf ):
    
    def __init__( self ):
        cwf_hdf.__init__( self )
        self.bands = None           # band name
        
    def determine_type( self ):     # get sensor type and set tags
        
        self.read_attributes()
	
        if self.attr.sensor ==  'avhrr': # determine if avhrr or gvar

            # get the data set's navigational correction transform matrix
            # trans = read_data_attribute( 'avhrr_ch1', 'nav_affine' )

            # set list of data bands
            self.bands = [ 'avhrr_ch1', 'avhrr_ch2', 'avhrr_ch3',
                           'avhrr_ch4', 'avhrr_ch5', 'avhrr_ch3a' ]

            self.channels =  '\n    AVHRR channel bands:\n'
            self.channels += '        ch1   : 00.58-00.68um at 1.1km\n'
            self.channels += '        ch2   : 00.72-01.00um at 1.1km\n'
            self.channels += '        ch3   : 03.55-03.93um at 1.1km\n'
            self.channels += '        ch4   : 10.30-11.30um at 1.1km\n'
            self.channels += '        ch5   : 11.50-12.50um at 1.1km\n'
            self.channels += '        ch3a  : 01.58-01.64um at 1.1km\n'
            
        elif self.attr.sensor == 'gvissr':

	    # navTrans = readNavTransform( "gvar_ch1" );
            # trans = read_data_attribute( 'gvar_ch1', 'nav_affine' )

            # determine which GOES satellite
            if self.satellite == 'goes-11':
                self.bands = [ 'gvar_ch1', 'gvar_ch2', 'gvar_ch3',
                               'gvar_ch4', 'gvar_ch5' ]

                self.channels =  '\n    GVISSR channel bands:\n'
                self.channels += '        ch1  : 00.53-00.79um at 1.0km\n'
                self.channels += '        ch2  : 03.78-04.03um at 4.0km\n'
                self.channels += '        ch3  : 06.47-07.04um at 8.0km\n'
                self.channels += '        ch4  : 10.23-11.25um at 4.0km\n'
                self.channels += '        ch5  : 11.58-12.50um at 4.0km\n'
                
            # TODO: determine spatial resolution and channel nonmenclature
            if self.satellite == 'goes-12':
                self.bands = [ 'gvar_ch1', 'gvar_ch2', 'gvar_ch3',
                               'gvar_ch4', 'gvar_ch6' ]

                self.channels =  '\n    GVISSR channel bands:\n'
                self.channels += '        ch1  : 00.53-00.77um at 1.0km\n'
                self.channels += '        ch2  : 03.76-04.03um at ?.?km\n'
                self.channels += '        ch3  : 05.77-07.34um at ?.?km\n'
                self.channels += '        ch4  : 10.23-11.24um at ?.?km\n'
                self.channels += '        ch6  : 12.96-13.72um at ?.?km\n'
                
        else:
            eprint( 'ag_hdf:unknown sensor type:',
                    self.attr.sensor, ' ...exiting' )
            sys.exit( 2 )

    def read_spectrum( self ):        # read spectral bands
                    
        nbands = len( self.bands )

        # make output a float32; allows NaN implementation, integer does not
        spect = np.empty( (self.attr.rows,self.attr.cols,nbands),
                          dtype=np.float32 )

        for i in range(0,nbands):
                    
            hdf = self.hdf_sd.select( self.bands[i] )
            temp = hdf.get() 

            # get NaN mask for input array (no Nan for integers)
            bool = temp == -32768     # NaN = -32768 (0xffff) given
            spect[:,:,i] = temp*0.01  # scale and make data float        

            # TODO: fix for gvissr
            if i in [0,1,5]:          # normalize albedo values 0,1
                spect[:,:,i] = spect[:,:,i]*0.01
            else:
                spect[:,:,i] = spect[:,:,i]+273.15 # make temps kelvin

            # replace with NaN
            masked = np.ma.array( spect[:,:,i], mask=bool )
            spect[:,:,i] = masked.filled( np.nan )

        return spect

    def read_navigation( self ):      # navigation bands lat,long
                    
        nav = np.empty( (self.attr.rows,self.attr.cols,2),
                        dtype=np.float32 )
        try:
            hdf = self.hdf_sd.select( 'latitude' )
            nav[:,:,0] = hdf.get()

            hdf = self.hdf_sd.select( 'longitude' )
            nav[:,:,1] = hdf.get()

            return nav

        except HDF4Error as e:
            eprint( e )
            return None

    def read_overlay( self ):        # graphics overlay
        overlay = np.empty( (self.attr.rows,self.attr.cols),
                            dtype=np.int8 )
        try:
            hdf = self.hdf_sd.select( 'graphics' )
            overlay[:,:] = hdf.get()

            return overlay

        except HDF4Error as e:
            eprint( e )
            return None
        
    def read_angle( self, name ):
                    
        try:
            hdf = self.hdf_sd.select( name )
            temp = hdf.get() 

            # get NaN mask for input array (no Nan for integers)
            bool = temp == -32768    # NaN = -32768 (0xffff) given

            # make data float        # TODO:get scale factor and NaN from hdf
            angle = temp*0.01        
                                     
            # replace with NaN
            masked = np.ma.array( angle, mask=bool )
            angle = masked.filled( np.nan )

            return angle

        except HDF4Error as e:
            eprint( e )
            return None

    def read_angles( self ):        # read sat,sun zenith and rel az
                    
        angles = np.empty( (self.attr.rows,self.attr.cols,4),
                           dtype=np.float32 )

        angles[:,:,0] = self.read_angle('sat_zenith')
        angles[:,:,1] = self.read_angle('sun_zenith')
        angles[:,:,2] = self.read_angle('rel_azimuth')
        angles[:,:,3] = self.read_angle('sat_azimuth')

        return angles

    def write_spectrum( self, spect ):
                    
        for i in range(0,6):         # only write out actual spectrum

            out = spect[:,:,i]               
            sensor = self.attr.sensor
            if sensor == 'avhrr':
                if i in [0,1,5]:
                    units = 'percent'
                    out = out*100.0  # undo normalizing
                else:
                    units = 'celsius'
                    out = out-273.15 # undo kelvin
            else:
                if i == 0:           # gvissr (not tested)
                    units = 'percent'        
                    out = out*100.0   
                else:
                    units = 'celsius'
                    out = out-273.15 # undo kelvin

            out = out*100.0          # apply scale factor

            # replace NaN with -32768
            masked = np.ma.masked_array( out, np.isnan(out) )
            out = masked.filled( -32768.0 )

            if i == 5 and sensor == 'avhrr':    # TODO: fix for gvissr
                channel = sensor + '_ch3a'
            else:
                channel = sensor + '_ch' + str(i+1)

            self.write_band( out.astype(np.int16), 
                             channel, units, self.attr.projection)

    def write_navigation( self, nav ):
                    
        if nav == None:
            return

        self.write_nav( nav[:,:,0], 'latitude', 'degrees', 
                        self.attr.projection )

        self.write_nav( nav[:,:,1], 'longitude', 'degrees', 
                        self.attr.projection )
        
    def write_angles( self, angles ):
                    
        if angles == None:
            return

        list = ['sat_zenith', 'sun_zenith', 'rel_azimuth', 'sat_azimuth']

        for i in range(0,4):
            out = angles[:,:,i]*100.0      # undo scale
            out = out + 0.5
            masked = np.ma.masked_array( out, np.isnan(out) ) 
            out = masked.filled( -32768.0 ) #flag NaNs
            self.write_sat_angles( out.astype(np.int16), list[i],
                                   'degrees',self.attr.projection )

    def write_overlay( self, graphics ):
                    
        if graphics == None:
            return

        self.write_graphics( graphics, self.attr.projection )
        
