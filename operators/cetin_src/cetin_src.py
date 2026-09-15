#! /usr/bin/env python

'''
@file cetin_src.py
@author Scott L. Williams.
@package POLI
@brief generate a cetin source image
@LICENSE
# 
#  cetin.py Copyright (C) 2010-2026 Scott L. Williams.
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

# generate a cetin image generator for poli 

cetin_src_copyright = 'cetin_src.py Copyright (c) 2010-2026 Scott L. Williams released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint

# determine if graphics (wx.python) can be enabled
try:
    import wx
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
# if not then assume batch implementation
except:
    from op import op
    operator = op
    #eprint( 'cetin_src: using non-graphics mode.' )

def get_name():
    return 'cetin_src'

# return an instance of 'cetin_src' class 
def instantiate():	
    return cetin_src()

class cetin_src_parameters( pio ):
    
    def __init__( self ):
        pass

    def print_params( self ):
        eprint( '\ncetin_src does not have parameters' )

class cetin_src( operator ):
    
    def __init__( self ): # initialize operator but no graphics
        
        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = cetin_src_parameters()  # not used yet

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
 
    def run( self ):            # override superclass run

        self.p.print_params()
        self.print_versions()
        self.source_name = 'cetin_src'
 
        # create a test image for SOM operators
        self.sink = np.empty( (128,128,6), dtype=np.uint8 )

        self.sink[:,0:32,0] = 21
        self.sink[:,32:128,0] = 0

        self.sink[:,0:64,1] = 42
        self.sink[:,64:128,1] = 63

        self.sink[0:32,:,2] = 105
        self.sink[32:128,:,2] = 84

        self.sink[:,0:96,3] = 126
        self.sink[:,96:128,3] = 147

        self.sink[0:96,:,4] = 168
        self.sink[96:128,:,4] = 189

        self.sink[0:64,:,5] = 210
        self.sink[64:128,:,5] = 231
 
    ####################################################################
    # gui section
    ####################################################################
   
    # overide since we are a source
    def apply_work( self ):
        
        self.run()            # run the operator

        # check if valid run output
        if not isinstance( self.sink, np.ndarray ):
            eprint( 'cetin_src: sink not set...returning' )
            return
        
        self.areal_index = None # set origin to center image

        # generic label
        self.band_tags = ['0','1','2','3', '4', '5']

    # scan panel parameters
    def read_params_from_panel( self ):
        return True

    # write parameters to panel
    def write_params_to_panel( self ):
        pass

    # initialize graphics
    def init_panel( self, benchtop ):       
        operator.init_panel( self, benchtop ) # start with basics
        
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: cetin_src.py' )
        eprint( '       -h, --help' )
        eprint( '       there are no other parameters' )
        eprint( '       output is stdout' )

    def set_params( self, argv ):

        try:                                
            opts, args = getopt.getopt( argv, 'h', ['help'] )
            
        except getopt.GetoptError as e:
            eprint( 'cetin: ' + str(e) )
            self.usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
 
####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    
    try:
        oper = instantiate()           # source point for pipe
        oper.set_params( sys.argv[1:] )
        oper.run()            
        oper.sink.dump( sys.stdout.buffer )   # send downstream
        
    except Exception as e:
        eprint( str(e) )
