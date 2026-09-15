'''
@file cwf_hdf.py
@author Scott L. Williams
@package POLI
@brief provides three distinct categories as numpy.arrays: spectral, navigational, and angle
@LICENSE
#
#  Copyright (C) 2010-2026 Scott L. Williams
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

cwf_hdf_copyright = 'cwf_hdf.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

# this class provides three distinct categories as numpy.arrays:
# spectral, navigational, and angle. spectral is 
# split out so that navigational correction can be applied before assembly. 
# navigation (lat,lon) is split out for both display reporting, metrics and 
# (possible) appending to spectral for viewing. finally the angles are split 
# out, likewise for analysis and/or viewing

import sys
from ezprint import eprint
from urllib import request

import numpy as np
from pyhdf.SD import SD, SDC, HDF4Error

# coastwatch hdf satellite attributes
class attr():
    
    def __init__( self ):
        
        self.satellite = None
        self.sensor = None
        self.origin = None
        self.history = None
        self.cwhdf_version = None
        self.pass_date = None          # nominally from 01/01/1970, day.xxx
        self.start_time = None
        self.projection_type = None
        self.projection = None
        self.gctp_sys = None
        self.gctp_zone = None
        self.gctp_parm = None
        self.gctp_datum = None
        self.et_affine = None
        self.rows = None
        self.cols = None
        self.polygon_latitude = None
        self.polygon_longitude = None
        self.pass_type = None          # day, night or day/night
        self.composite = None

class cwf_hdf():

    def __init__( self ):
        self.hdf_sd = None
        self.attr = attr()

    def open_file( self, filepath, mode='READ' ):     # hdf file
        
        if mode == 'CREATE':
            mode = SDC.WRITE|SDC.CREATE|SDC.TRUNC
            
        elif mode == 'WRITE':
            mode = SDC.WRITE
            
        elif mode == 'READ':
            mode = SDC.READ
        
        else:
            eprint( 'cwf_hdf: unknown mode:', mode, ' returning' )
            return
    
        # string cast is necessary for SD
        # when text is processed through textctrl FileDrop
        self.hdf_sd = SD( str(filepath), mode )

    def close_file( self ):
        
        self.hdf_sd.end()
        self.hsf_sd = None

    def get_attr( self, name ):        # get single attribute by name
        
        if self.hdf_sd == None:
            eprint( 'cwf_hdf: get_attr: hdf file not open' )
            return None
        
        try:
            attr = self.hdf_sd.attr( name )  
            attr.index()               # gotta do this first
            return attr.get()

        except HDF4Error as e:
            eprint( 'cwf_hdf: get_attr: HDF4Error: name:' + name + '\n', e )
            return None

    def read_attributes( self ):       # read satellite attributes
        
        if self.hdf_sd == None:
            eprint( 'cwf_hdf: file not open' )
            return

        self.attr.satellite = self.get_attr( 'satellite' )
        self.attr.sensor = self.get_attr( 'sensor' )
        self.attr.origin = self.get_attr( 'origin' )
        self.attr.history = self.get_attr( 'history' )
        self.attr.cwhdf_version = self.get_attr( 'cwhdf_version' )

        # get these as either singletons or lists
        self.attr.pass_date = self.get_attr( 'pass_date' )
        self.attr.start_time = self.get_attr( 'start_time' )

        self.attr.projection_type = self.get_attr( 'projection_type' )
        self.attr.projection = self.get_attr( 'projection' )
        self.attr.gctp_sys = self.get_attr( 'gctp_sys' )
        self.attr.gctp_zone = self.get_attr( 'gctp_zone' )
        self.attr.gctp_parm = self.get_attr( 'gctp_parm' )
        self.attr.gctp_datum = self.get_attr( 'gctp_datum' )
        self.attr.et_affine = self.get_attr( 'et_affine' )
        self.attr.rows = self.get_attr( 'rows' )
        self.attr.cols = self.get_attr( 'cols' )
        self.attr.polygon_latitude = self.get_attr( 'polygon_latitude' )
        self.attr.polygon_longitude = self.get_attr( 'polygon_longitude' )
        self.attr.pass_type = self.get_attr( 'pass_type')
        #self.attr.composite = self.get_attr( 'composite')

    def create_attr( self, data, name, type, values ): # create and set an attr
        
        try:
            attr = data.attr( name )
            attr.set( type, values )
        except HDF4Error as e:
            eprint( 'create_attr: HDF4Error:\n', e )

    def write_attributes( self ):      # write satellite attributes
        
        self.create_attr( self.hdf_sd, 'satellite',
                          SDC.CHAR, self.attr.satellite )
        
        self.create_attr( self.hdf_sd, 'sensor',
                          SDC.CHAR, self.attr.sensor )
        
        self.create_attr( self.hdf_sd, 'origin',
                          SDC.CHAR, self.attr.origin )
        
        self.create_attr( self.hdf_sd, 'history',
                          SDC.CHAR, self.attr.history )
        
        self.create_attr( self.hdf_sd, 'cwhdf_version',
                          SDC.CHAR, self.attr.cwhdf_version)
        
        self.create_attr( self.hdf_sd, 'pass_type',
                          SDC.CHAR, self.attr.pass_type )

        self.create_attr( self.hdf_sd, 'pass_date',
                          SDC.INT32, self.attr.pass_date )
        self.create_attr( self.hdf_sd, 'start_time',
                          SDC.FLOAT64, self.attr.start_time )

        self.create_attr( self.hdf_sd, 'projection_type',
                          SDC.CHAR, self.attr.projection_type )
        
        self.create_attr( self.hdf_sd, 'projection',
                          SDC.CHAR, self.attr.projection )
        
        self.create_attr( self.hdf_sd, 'gctp_sys',
                          SDC.INT32, self.attr.gctp_sys )
        
        self.create_attr( self.hdf_sd, 'gctp_zone',
                          SDC.INT32, self.attr.gctp_zone )
        
        self.create_attr( self.hdf_sd, 'gctp_parm',
                          SDC.FLOAT64, self.attr.gctp_parm )
        
        self.create_attr( self.hdf_sd, 'gctp_datum',
                          SDC.INT32, self.attr.gctp_datum )
        
        self.create_attr( self.hdf_sd, 'et_affine',
                          SDC.FLOAT64, self.attr.et_affine )
        
        self.create_attr( self.hdf_sd, 'rows',
                          SDC.INT32, self.attr.rows )
        
        self.create_attr( self.hdf_sd, 'cols',
                          SDC.INT32, self.attr.cols )
        
        self.create_attr( self.hdf_sd, 'polygon_latitude',
                          SDC.FLOAT64, self.attr.polygon_latitude )
        
        self.create_attr( self.hdf_sd, 'polygon_longitude',
                          SDC.FLOAT64, self.attr.polygon_longitude )
        '''
        if self.attr.composite == 'true':
            self.create_attr( self.hdf_sd, 'composite',
                              SDC.CHAR, self.attr.composite )
        '''
    def format_hour( self, time ):        # format time in secs for readability
        hr = int(time/3600)
        min = int((time-(hr*3600))/60)
        sec = int(time-(hr*3600)-(min*60))
            
        time_start = '%02d'%hr + ':' + '%02d'%min + ':' + '%02d'%sec + ' '
        return time_start
        
    def format_attributes( self ):        # for printing
        
        attributes = []

        attributes.append( '\tsatellite:\t\t\t' + self.attr.satellite )
        attributes.append( '\tsensor:\t\t\t' + self.attr.sensor )
        attributes.append( '\torigin:\t\t\t' + self.attr.origin )
        attributes.append( '\tpass type:\t\t' + self.attr.pass_type )
        attributes.append( '\tversion:\t\t\t' + self.attr.cwhdf_version )
        attributes.append( '\tprojection:\t\t' + self.attr.projection )
        attributes.append( '\tprojection_type:\t' + self.attr.projection_type )

        # handle date(s); check if list or int

        # TODO: figure out calendar date from epoch days
        #if type( self.attr.pass_date ) == int:
        if isinstance( self.attr.pass_date, int ):
            attributes.append( '  pass date:       ' + str(self.attr.pass_date))
            time_start = self.format_hour( self.attr.start_time )
            attributes.append( '  start_time:      ' + time_start + ' UTC' )
            
        else:
            date_pass = ''                        
            time_start = ''
            for i in range( 0, len(self.attr.pass_date)):

                date_pass = date_pass + '%9d'%self.attr.pass_date[i]
                time_start = time_start + self.format_hour( 
                    self.attr.start_time[i] )
            attributes.append( '  pass date:       ' + date_pass )
            attributes.append( '  start_time:      ' + time_start + ' UTC' )

        return attributes

    def write_band( self, band, name, units, coordsys ):
        
        height,width = band.shape
        data = self.hdf_sd.create( name, SDC.INT16, (height,width) )
        data.setcompress( SDC.COMP_DEFLATE )

        data[:] = band                                # write data out

        dim0 = data.dim(0)
        dim0.setname('rows')
        dim1 = data.dim(1)
        dim1.setname('cols')

        self.create_attr( data, 'long_name', SDC.CHAR, name )
        self.create_attr( data, 'units', SDC.CHAR, units )
        self.create_attr( data, 'coordsys', SDC.CHAR, coordsys )

        data.setfillvalue( -32768 )

        self.create_attr( data, 'missing_value', SDC.INT16, -32768 )
        self.create_attr( data, 'scale_factor', SDC.FLOAT64, 0.01 )
        self.create_attr( data, 'scale_factor_err', SDC.FLOAT64, 0.0 )
        self.create_attr( data, 'add_offset', SDC.FLOAT64, 0.0 )
        self.create_attr( data, 'add_offset_err', SDC.FLOAT64, 0.0 )
        self.create_attr( data, 'calibrated_nt', SDC.INT32, 0 )
        self.create_attr( data, 'fraction_digits', SDC.INT32, 2 )
        
        data.endaccess()                              # close 

    def write_nav( self, nav, name, units, coordsys ):
        
        height,width = nav.shape
        data = self.hdf_sd.create( name, SDC.FLOAT32, (height,width) )
        data.setcompress( SDC.COMP_DEFLATE )

        data[:] = nav                                 # write data out

        dim0 = data.dim(0)
        dim0.setname('rows')
        dim1 = data.dim(1)
        dim1.setname('cols')

        self.create_attr( data, 'long_name', SDC.CHAR, name )
        self.create_attr( data, 'units', SDC.CHAR, units )
        self.create_attr( data, 'coordsys', SDC.CHAR, coordsys )

        data.setfillvalue( np.nan )        

        self.create_attr( data, 'missing_value', SDC.FLOAT32, np.nan )
        self.create_attr( data, 'fraction_digits', SDC.INT32, 6 )

        data.endaccess()                              # close 

    def write_sat_angles( self, angles, name, units, coordsys ):
        
        height,width = angles.shape
        data = self.hdf_sd.create( name, SDC.INT16, (height,width) )
        data.setcompress( SDC.COMP_DEFLATE )

        data[:] = angles
        dim0 = data.dim(0)
        dim0.setname('rows')
        dim1 = data.dim(1)
        dim1.setname('cols')

        self.create_attr( data, 'long_name', SDC.CHAR, name )
        self.create_attr( data, 'units', SDC.CHAR, units )
        self.create_attr( data, 'coordsys', SDC.CHAR, coordsys )

        data.setfillvalue( -32768 )
        
        self.create_attr( data, 'missing_value', SDC.INT16, -32768 )
        self.create_attr( data, 'scale_factor', SDC.FLOAT64, 0.01 )
        self.create_attr( data, 'scale_factor_error', SDC.FLOAT64, 0.0 )
        self.create_attr( data, 'add_offset', SDC.FLOAT64, 0.0 )
        self.create_attr( data, 'add_offset_err', SDC.FLOAT64, 0.0 )
        self.create_attr( data, 'calibrated_nt', SDC.INT32, 0 )
        self.create_attr( data, 'fraction_digits', SDC.INT32, 2 )

        data.endaccess()                              # close 

    def write_graphics( self, graphics, coordsys ):
        
        height,width = graphics.shape
        data = self.hdf_sd.create( 'graphics', SDC.INT8, (height,width) )
        data.setcompress( SDC.COMP_DEFLATE )

        data[:] = graphics                            # write data out

        dim0 = data.dim(0)
        dim0.setname('rows')
        dim1 = data.dim(1)
        dim1.setname('cols')

        self.create_attr( data, 'long_name', 
                          SDC.CHAR, 'graphics overlay planes' )
        self.create_attr( data, 'coordsys', SDC.CHAR, coordsys )

        data.setfillvalue( 0 )

        self.create_attr( data, 'missing_value', SDC.INT8, 0 )
        self.create_attr( data, 'scale_factor', SDC.FLOAT64, 1.0 )
        self.create_attr( data, 'scale_factor_err', SDC.FLOAT64, 0.0 )
        self.create_attr( data, 'add_offset', SDC.FLOAT64, 0.0 )
        self.create_attr( data, 'add_offset_err', SDC.FLOAT64, 0.0 )
        self.create_attr( data, 'calibrated_nt', SDC.INT32, 0 )
        self.create_attr( data, 'fraction_digits', SDC.INT32, 0 )

        data.endaccess()                              # close 

    # create a numpy RGBA image from overlay buffer
    def make_overlay_image( self, overlay_buf, 
                            setgrid, setcoast, setboundaries ):

        #if overlay_buf == None:
        #if type( overlay_buf ) is not np.ndarray:
        if not isinstance( overlay_buf, np.ndarray ):
            return

        height,width = overlay_buf.shape

        rgba = np.zeros( (height,width,4), dtype=np.uint8 )

        if setgrid == True:
            bool = overlay_buf[:,:] & 0x02
            masked = np.ma.array( rgba[:,:,1], mask=bool )
            rgba[:,:,1] = masked.filled( 0xff )      # green buf
            rgba[:,:,3] = rgba[:,:,1]                # set to not transparent

        if setcoast == True:
            bool = overlay_buf[:,:] & 0x04
            masked = np.ma.array( rgba[:,:,0], mask=bool )
            rgba[:,:,0] = masked.filled( 0xff )      # red buf
            rgba[:,:,3] = rgba[:,:,0] | rgba[:,:,3]  # carry all transparencies

        if setboundaries == True:
            bool = overlay_buf & 0x10

            masked = np.ma.array( rgba[:,:,2], mask=bool )
            rgba[:,:,2] = masked.filled( 0xff )      # blue buf
            rgba[:,:,3] = rgba[:,:,2] | rgba[:,:,3]

        return rgba
