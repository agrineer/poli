#! /usr/bin/env python

'''
@file mdust.py
@author Scott L. Williams
@package POLI
@brief Miller dust detection
@LICENSE
#
# Copyright (c) 2010-2026 Scott L. Williams

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
Miller dust detectection implementation 
a consolidated technique for enhancing desert dust storms with MODIS'
S.D. Miller, geophysical research letters vol.30, #20
'''
mdust_copyright = 'mdust.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
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
    eprint( 'mdust: using non-graphics mode.' )

def get_name(): 
    return 'mdust'

# return an instance of 'mdust' class 
def instantiate():	
    return mdust()

class mdust_parameters( pio ):
    
    def __init__( self ):
        
        self.stype = 'land'               # water, land
        self.use_ch26 = False
        self.redonly = False

    def print_params( self ):
        
        eprint( '\nparameters for mdust:' )
        eprint( '                type =', self.stype )
        eprint( '            use_ch26 =', self.use_ch26 )
        eprint( '             redonly =', self.redonly )

class mdust( operator ):
    
    def __init__( self ):      # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = mdust_parameters()
        
        #self.fout = sys.stderr       # used for batch ouput, otherwise stderr

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
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

    def brightness( self, band, index ):

        # thermal band data are converted from radiance to brightness 
        # (apparent blackbody ) temperature by inverting Planck's equation:
        #  
        #                T = C2 / ( lmda*ln[(C1 / (lmda^5*R*10^6))+ 1.0] )
        #
        # (Gumley, 1994),(Riggs,2001)
        # (Alley, JPL, Algorithm Theoretical Basis Document for
        #  Brightness Temperature, 1999)
        #
        # where    T  = brightness temperature in Kelvin
        #          C1 = 2*h*c^2 = 1.1910439 * 10^-16 W m^-2
        #               Plank's first constant for spectral rad
        #          C2 = (h*c)/k = 1.4387686 * 10^-2 m K
        #               Planks's second constant
        #          lmda = center wavelength in m
        #          R    = Planck radiance in W m^-2 sr^-1 um^-1

        if index not in [31,32]:
            eprint( 'mdust: brightness: bad index', index )
            return None

        wavemap = {31: 11.03e-6, 32: 12.02e-6}  # channel center wavelengths (m)
        lmda = wavemap[ index ]                 # get center frequency
        
        R = band*1e6       # build log term
        denom = R*(lmda**5)
        prod  = 1.1910439e-16/denom
        term = prod + 1.0
        ln_term = np.log( term )

        ndenom = ln_term*lmda

        return 1.4387686e-2/ndenom

    # convert band range to floor to ceiling
    def scale_band( self, image, floor, ceiling ):
        min = np.nanmin( image )      # get values to scale by
        max = np.nanmax( image )      # ignoring nan
        if max == min :               # check for constant values
            scale = 0.0 	      # make image a surface plane
            c = 0.0

        elif np.isinf( min ) or np.isinf( max ):
            scale = 0.0 	      # make image a surface plane
            c = 0.0

        else :
            scale = (ceiling-floor)/(max-min) 
            c = -scale*min

        return image*scale + c

    def overland( self ):

        # convert thermal radiances to brightness temps
        # ch. 31 => band 5  ch. 32 => band 6
        T31 = self.brightness( self.source[:,:,5], 31 )
        T32 = self.brightness( self.source[:,:,6], 32 )

        diff = T32 - T31
        L1 = np.clip( diff, -2.0, 2.0 ) 
        L1 = self.scale_band( L1, 0.0, 1.0 )

        # get bounds for L2
        Tmax = np.nanmax( T31 )
        if Tmax < 301.0:
            Tdyn = Tmax - 21
        else:
            Tdyn = (Tmax-273.0)/4.0 + 273.0

        L2 = np.clip( T31, Tdyn, Tmax )
        L2 = self.scale_band( L2, 0.0, 1.0 )

        # L3
        R1 = self.source[:,:,0]   # ch.1 => band 0
        R3 = self.source[:,:,2]   # ch.3 => band 2
        R4 = self.source[:,:,3]   # ch.4 => band 3

        L3 = R1*2
        L3 = L3-R3
        L3 = L3-R4
        L3 = L3-L2

        L3 = np.clip( L3, -1.5, 0.25 )
        L3 = self.scale_band( L3, 0.0, 1.0 )

        # L4
        L4 = np.ones( self.source[:,:,4].shape, dtype=np.float32 )
        bool = self.source[:,:,4] > 0.05  # ch.26 => band 4
        masked = np.ma.array( L4, mask=bool )
        L4 = masked.filled( 0.0 )
        
        result = L1 + L3
        if self.p.use_ch26:
            result = result - L4
            
        result = result + 1
        result = result - L2
        result = np.clip( result, 1.3, 2.7 )
        return result
         
    # USAGE: read channels 1,2,3,4,26,31,32 from projmod_source
    #        set reflectance.(use projmod_source, scrb_modis_1km.hdf)
    def run( self ):
        
        self.p.print_params()            # report parameters used when running
        self.print_versions()
         
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

        # blue  ch.3 => band 2;  log10 adjusted reflectances
        # TODO: remove rayleigh scattering
        blue = np.log10( self.source[:,:,2] )
        self.sink[:,:,2] = np.clip( blue, -1.45, 0.0 )

        # green ch.4 => band 3
        green = np.log10( self.source[:,:,3] )
        self.sink[:,:,1] = np.clip( green, -1.45, 0.0 )

        if self.p.stype == 'water':
            self.sink[:,:,0] = self.overwater()
        else:
            self.sink[:,:,0] = self.overland()

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):       # scan panel parameters
        
        self.p.use_ch26 = self.c_use_ch26.GetValue()
        self.p.redonly = self.c_redonly.GetValue()

        if self.r_overwater.GetValue():
            self.p.type = 'water'
        elif self.r_overland.GetValue():
            self.p.type = 'land'

        return True

    def write_params_to_panel( self ):        # write parameters to panel
        
        self.c_use_ch26.SetValue( self.p.use_ch26 )
        self.c_redonly.SetValue( self.p.redonly )
        
        if self.p.stype == 'water':
            self.r_overwater.SetValue( True )
        elif self.p.stype == 'land':
            self.r_overland.SetValue( True )

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

        self.c_use_ch26 = wx.CheckBox( self.p_client, -1, 'use Ch.26' )
        self.c_use_ch26.SetToolTip( 'use reflective 1.36-1.39' )
        v_sizer.Add( self.c_use_ch26 )

        self.c_redonly = wx.CheckBox( self.p_client, -1, 'red only' )
        self.c_redonly.SetToolTip( 'output only red buffer' )
        v_sizer.Add( self.c_redonly )

        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    ############################################################
    # command line options for batch implementation
    ############################################################

    def usage( self ):
        eprint( 'usage: mdust.py' )
        eprint( '       -h, --help' )
        eprint( '       -u, --use_ch26' )
        eprint( '       -r, --redonly' )
        eprint( '       -t <land,water>, --type=<land,water>' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hurt:p:',
                                        ['help','use_ch26','redonly','type=',
                                         'params='] )
        except getopt.GetoptError as e:
            eprint( 'mdust: ' + str(e) )  
            self.usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:
                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            elif opt in ( '-u', '--use_ch26' ):
                self.p.use_ch26 = True

            elif opt in ( '-r', '--redonly' ):
                self.p.redonly = True
  
            elif opt in ( '-t', '--type' ):
                if arg not in ( 'water','land' ):
                    eprint( 'mdust: unknown type:', arg, ' ...exiting' )
                    sys.exit( 2 )
                self.p.stype = arg

            elif opt in ('-p', '--params'):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'mdust: set_params: bad params file read...exiting' )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':

    try:
        import tempfile

        # numpy needs to 'seek' on the file to load
        # so read from stdin to temporary file
        temp = tempfile.NamedTemporaryFile( delete_on_close=True )
        temp.write( sys.stdin.buffer.read() )
        temp.seek(0,0)

        oper = instantiate()   
        oper.set_params( sys.argv[1:] )

        # load the numpy array data; can use memory map here
        oper.source = np.load( temp, allow_pickle=True )
        oper.run()

        # send down stream 
        oper.sink.dump( sys.stdout.buffer )
  
    except Exception as e:
        eprint( str(e) )
