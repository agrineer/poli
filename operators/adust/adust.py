#! /usr/bin/env python3

'''
@file adust.py
@author Scott L. Williams.
@package POLI
@brief miller dust algorithm AVHRR implementation 
@LICENSE

#  adust.py
# 
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
@sections DESCRIPTION
 miller dust algorithm AVHRR implementation 
# 'A consolidated technique for enhancing desert dust storms with MODIS'
# S.D. Miller, geophysical research letters vol.30, #20
'''

adust_copyright = 'adust.py Copyright (c) 2010-2025 Scott L. Williams ' + \
                  'released under GNU GPL V3.0'

import os
import sys
import math
import getopt
import numpy as np
from ezprint import eprint

# determine if graphics can be enabled
try:
    import wx
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
# if not then assume non-graphics implementaion
except:
    from op import op
    operator = op
    eprint( 'adust: using non-graphics mode.' )

def get_name(): 
    return 'adust'

# return an instance of 'adust' class 
def instantiate():	
    return adust( get_name() )

class adust_parameters():

    def __init__( self ):
        self.stype = 'land'           # water, land
        #self.redonly = False         
        self.use_3um = False
        self.noenhance = False

    def print_params( self ):

        eprint( '\nparameters for adust:' )
        eprint( '    surface type =', self.stype )
        #eprint( '    red only     =', self.redonly )
        eprint( '    use_3um      =', self.use_3um )
        eprint( '    noenhance    =', self.noenhance )
         
#------------------------------------------------------------------------------

class adust( operator ):
    
    def __init__( self, name ):      # initialize op_panel but no graphics
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = adust_parameters()
 
    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
 
    def overwater( self ):

        # normalized difference
        numerator = self.source[:,:,1] - self.source[:,:,2]
        denominator = self.source[:,:,1] + self.source[:,:,2]
        diff = numerator/denominator

        # red buffer
        red = np.log10( diff )
        return np.clip( red, -0.40, 0.15 )

    # convert band range from floor to ceiling
    def scale_band( self, image, floor=0.0, ceiling=1.0 ):
        
        nmin = np.nanmin( image )      # get values to scale by
        nmax = np.nanmax( image )      # ignoring nan
        if nmax == nmin:               # check for constant values
            scale = 0.0 	       # make image a surface plane
            c = 0.0

        elif np.isinf( nmin ) or np.isinf( nmax ):
            scale = 0.0 	      # make image a surface plane
            c = 0.0

        else:
            scale = (ceiling-floor)/(nmax-nmin) 
            c = -scale*nmin

        return image*scale + c

    def overland( self ):

        band4 = self.source[:,:,4] - 273.15     # work in celsius
        band3 = self.source[:,:,3] - 273.15

        diff = band4 - band3                    # 12um-11um
        max = np.nanmax( diff )
        L1 = np.clip( diff, 0.0, max )          # clamp neg values to enhance
                                                # positive range
        if self.p.noenhance:
            return self.scale_band( L1 )       

        # enhancement as per modified miller
        result = self.scale_band( L1 )          # set baseline

        # get bounds for L2 (modified 11um band)
        Tmax = np.nanmax( band3 )               # see miller paper
        if Tmax < 28:                           
            Tdyn = Tmax - 21
            eprint( 'Tmax < 28', Tmax, Tdyn )
        else:
            Tdyn = Tmax/4.0 
            eprint( 'Tmax >= 28', Tmax, Tdyn )

        L2 = np.clip( band3, Tdyn, Tmax )
        L2 = self.scale_band( L2, 0.0, 1.0 )

        if self.p.use_3um:                      # remove water vapor influence

            L4 = np.ones( self.source[:,:,2].shape, dtype=np.float32 )
            s3um = self.source[:,:,2]
            s3um = self.scale_band( s3um )
            bool = s3um > 0.65
            masked = np.ma.array( L4, mask=bool )
            L4 = masked.filled( 0.0 )
            result = result - L4
            
        result = result - L2                    # strengthen 11um effect
        result = np.clip( result, 0.0001, 2.7 ) # clamp for log
        result = np.log( result )               # cluster values
        result = self.scale_band( result )      # scale 0-1
        return result
                
    def NDVI( self, red, nir ):        

        # subtract red from nir for numerator
        numerator = np.empty( red.shape, dtype=np.float32 )
        numerator = red - nir

        # add red and nir for denominator
        denominator = np.empty( red.shape, dtype=np.float32 )
        denominator = red + nir
        
        ndvi = numerator/denominator
        scaled_band = self.scale_band( ndvi, 0.0, 1.0 ) # sw
        return 1.0 - scaled_band                # complement values

    def run( self ):

        self.p.print_params()            # report parameters used when running
        self.print_versions()

        if self.p.stype == 'water':
            self.sink = self.overwater()
        else:
            self.sink = self.overland()

        height,width = self.sink.shape
        self.sink.shape = height,width,1
        return

        ''' attempt to make RGB output not so good
        if self.p.redonly:               # out red buffer only
            
            if self.p.stype == 'water':
                self.sink = self.overwater()
            else:
                self.sink = self.overland()

            height,width = self.sink.shape
            self.sink.shape = height,width,1
            return

        # set up outgoing RGB image
        height,width,nbands = self.source.shape
        self.sink = np.zeros( (height,width,3), dtype=np.float32 )

        # AVHRR does not have a green channel; use NDVI instead
        ndvi = self.NDVI( self.source[:,:,0], self.source[:,:,1] )
        green = np.log( ndvi )
        self.sink[:,:,1] = np.clip( green, -1.45, 0.0 )

        # AVHRR does not have a blue channel; use complemented 3um instead
        blue = self.scale_band( self.source[:,:,2], 0.0, 1.0 )
        #blue = 1.0 - blue
        blue = np.log( blue )
        self.sink[:,:,2] = np.clip( blue, -1.45, 0.0 )
        
        # use dust detected values for red buffer
        if self.p.stype == 'water':
            self.sink[:,:,0] = self.overwater()
                
        elif self.p.stype == 'land':
            self.sink[:,:,0] = self.overland()
            
        else:
            eprint( 'adust: unknown surface type:', self.p.stype,
                    ' exiting' )
            sys.exit( 2 )
        '''      
            
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):       # scan panel parameters
        
        self.p.use_3um = self.c_use_3um.GetValue()
        #self.p.redonly = self.c_redonly.GetValue()
        self.p.noenhance = self.c_noenhance.GetValue()

        if self.r_overwater.GetValue():
            self.p.stype = 'water'
            
        elif self.r_overland.GetValue():
            self.p.stype = 'land'

        return True

    def write_params_to_panel( self ):        # write parameters to panel
        
        self.c_noenhance.SetValue( self.p.noenhance )
        self.c_use_3um.SetValue( self.p.use_3um )
        #self.c_redonly.SetValue( self.p.redonly )
        
        if self.p.stype == 'water':
            self.r_overwater.SetValue( True )
            
        elif self.p.stype == 'land':
            self.r_overland.SetValue( True )

        else:
            eprint( 'adust: write_params_to_panel: unknown surface type' )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )

        self.r_overwater = wx.RadioButton( self.p_client, -1, 'overwater', 
                                           style = wx.RB_GROUP )
        self.r_overwater.SetToolTip( 'detect dust over water' )
        v_sizer.Add( self.r_overwater )

        self.r_overland = wx.RadioButton( self.p_client, -1, 'overland' )

        self.r_overland.SetToolTip( 'detect dust over land' )
        v_sizer.Add( self.r_overland )

        self.c_use_3um = wx.CheckBox( self.p_client, -1, 'use 3um' )
        self.c_use_3um.SetToolTip( 'use freq. 3um' )
        v_sizer.Add( self.c_use_3um )

        '''
        self.c_redonly = wx.CheckBox( self.p_client, -1, 'red only' )
        self.c_redonly.SetToolTip( 'output only red buffer' )
        v_sizer.Add( self.c_redonly )
        '''
        
        self.c_noenhance = wx.CheckBox( self.p_client, -1, 'no enhance' )
        self.c_noenhance.SetToolTip( 'use diff only' )
        v_sizer.Add( self.c_noenhance )

        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    ############################################################
    # command line options for batch implementation
    ############################################################

    def usage( self ):
        
        eprint( 'usage: adust.py' )
        eprint( '   -h, --help' )
        #eprint( '   -r, --red' )
        eprint( '   -u, --use_3um' )
        eprint( '   -s stype, --stype=stype' )
        eprint( '      surface type: either water or land' )
        eprint( '   -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input == stdin, output == stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hruns:p:',
                                        ['help','redonly','use_3um',
                                         'noenhance','stype=','param=' ])
        except getopt.GetoptError as e:
            eprint( 'blur: ' + str(e) )
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            '''
            if opt in ( 'r', '--redonly' ):
                self.p.redonly = True\
            '''
            
            if opt in ( 'u', '--use_3um' ):
                self.p.use_3um = True

            if opt in ( 'n', '--noenhance' ):
                self.p.noenhance = True
               
            elif opt in ( '-s', '--stype' ):
                
                if arg not in ( 'water', 'land'):
                    eprint( 'adust: unknown surface type:', arg,
                            ' ...exiting' )
                    sys.exit( 2 )

                self.p.stype = arg
                     
            elif opt in ('-p', '--params'):
                params = arg  

        if params != None:
            
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'blur: set_params: bad params file read...exiting' )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    import tempfile

    # numpy needs to 'seek' in the file to load
    # so read from stdin to temporary file first
    temp_name = next( tempfile._get_candidate_names() ) + '.tmp'
    temp = open( temp_name, 'wb' )
    temp.write( sys.stdin.buffer.read() )
    temp.close()

    try:
        oper = instantiate()   
        oper.set_params( sys.argv[1:] )

        # load the numpy array data; can use memory map here
        oper.source = np.load( temp_name, allow_pickle=True )
        oper.run()

        # send down stream 
        oper.sink.dump( sys.stdout.buffer )
        
    except Exception as e:
        eprint( str(e) )
 
    os.remove( temp_name )

