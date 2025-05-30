#! /usr/bin/env python3

'''
@file thrsh_yen.py
@author Scott L. Williams.
@package POLI
@brief skimage yen thresholding
@LICENSE
#
#  thrsh_yen.py Copyright (C) 2010-2025 Scott L. Williams.
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
Threshold value based on Yen’s method.
Returns:

    threshold : float applied towards image

    Upper threshold value. All pixels with an intensity higher than this
    value are assumed to be foreground.
'''

thrsh_yen_copyright = 'thrsh_yen.py Copyright (c) 2010-2025 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import skimage
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
    eprint( 'thrsh_yen: using non-graphics mode.' )

def get_name():
    return 'thrsh_yen'

# return an instance of 'thrsh_yen' class 
def instantiate():	
    return thrsh_yen( get_name() )

class thrsh_yen_parameters( pio ):
    
    def __init__( self ):
        self.binary = False
        
    def print_params( self ):
        
        eprint( '\nparameters for thrsh_yen:' )
        eprint( '      binary =', self.binary  )
        
# ----------------------------------------------------------------------------

class thrsh_yen( operator ):
    
    def __init__( self, name ):         # initialize op_panel but no graphics

        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = thrsh_yen_parameters()
        
    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy   =', np.version.version )
        eprint( '   skimage =', skimage.__version__)

    def run( self ):                    # override superclass run

        self.p.print_params()           # report parameters used
        self.print_versions()

        t_yen = skimage.filters.threshold_yen( self.source )
        
        mask = self.source > t_yen      # boolean mask
               
        if self.p.binary: # show binary image
            self.sink = mask
        else:
            self.sink = self.source * mask
      
    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):
        self.p.binary = self.c_binary.GetValue()
        return True

     # write parameters to panel
    def write_params_to_panel( self ):
        self.c_binary.SetValue( self.p.binary )
 
    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1,10 )

        self.c_binary = wx.CheckBox( self.p_client, 0, 'binary image' )
        v_sizer.Add( self.c_binary )
        
        self.p_client.SetSizer( v_sizer )
        
        self.write_params_to_panel()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        eprint( 'usage: thrsh_yen' )
        eprint( '       -h, --help' )
        eprint( '       -b, --binary ' )
        eprint( '             for binary output 0/255 ')
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hbp:', 
                                        ['help','binary','params=' ])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)
                
            elif opt in ( '-b', '--binary' ):
                self.p.binary = True

            elif opt in ( '-p', '--params' ):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'thrsh_yen: cannot read parm file:', params,
                        ' ...exiting' )
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
        eprint( e )
 
    os.remove( temp_name )
