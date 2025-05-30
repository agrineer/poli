#! /usr/bin/env python3

'''
@file derivative.py
@author Scott L. Williams.
@package POLI
@brief derivative operator
@LICENSE
#
#  derivative.py Copyright (C) 2010-2025 Scott L. Williams.
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

derivative_copyright = 'derivative.py Copyright (c) 2010-2025 Scott L. Williams, released under GNU GPL V3.0'

#  derivative operator for poli 

import os
import sys
import scipy
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
    eprint( 'derivative: using non-graphics mode.')

def get_name(): 
    return 'derivative'

# return an instance of 'derivative' class 
def instantiate():	
    return derivative( get_name() )

class derivative_parameters( pio ):       # hold arguments values here
    
    def __init__( self ):
        self.ddir = 'x'                   # directions are: x, y, xy

    def print_params( self ):
        eprint( '\nparameters for derivative:' )
        eprint( '    dir =', self.ddir )

# ----------------------------------------------------------------------------

class derivative( operator ):
    
    def __init__( self, name ):      # initialize op_panel but no graphics
        
        operator.__init__( self, name )
        self.__version__ = '20250416'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = derivative_parameters()

    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
        eprint( '   scipy =', scipy.version.version )
        
    def run( self ):                 # override superclass run

        self.p.print_params()        # report parameters when running
        self.print_versions()

        self.sink = np.empty( self.source.shape,     
                              dtype=np.float32 ) # make output float

        if self.p.ddir == 'x':
            kernel = np.array( [1.0, -1.0] )
            kernel.shape = 2,1,1
            
        elif self.p.ddir == 'y':
            kernel = np.array( [1.0, -1.0] )
            kernel.shape = 1,2,1
            
        elif self.p.ddir == 'xy':
            kernel = np.array( [1.0, 0.0, 0.0, -1.0] )
            kernel.shape = 2,2,1
            
        else:
            eprint( 'derivative: unknown option:', self.p.ddir )
            sys.exit( 1 )

        scipy.ndimage.convolve( self.source, kernel, output=self.sink )

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        
        if self.r_dxy.GetValue():
            self.p.ddir = 'xy'
            
        if self.r_dx.GetValue():
            self.p.ddir = 'x'
            
        elif self.r_dy.GetValue():
            self.p.ddir = 'y'

        return True

    def write_params_to_panel( self ):   # write parameters to panel
        
        if self.p.ddir == 'xy':
            self.r_dxy.SetValue( True )
            
        if self.p.ddir == 'x':
            self.r_dx.SetValue( True )
            
        if self.p.ddir == 'y':
            self.r_dy.SetValue( True )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        # make radio panel
        p_radio = wx.Panel( self.p_client, -1, (10,2), (100,90) )

        sizer = wx.GridBagSizer( 2, 1 )

        #  mark the beginning of the group with wx.RB_GROUP
        self.r_dx = wx.RadioButton( p_radio, -1, 'dx', 
                                    style = wx.RB_GROUP )

        self.r_dy = wx.RadioButton( p_radio, -1, 'dy' )
 
        self.r_dxy = wx.RadioButton( p_radio, -1, 'dxy' )
 
        self.r_dy.SetValue( True )

        sizer.Add( self.r_dx, (0,0) )
        sizer.Add( self.r_dy, (1,0) )
        sizer.Add( self.r_dxy, (2,0) )

        p_radio.SetSizer( sizer )

        self.write_params_to_panel()
   
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: derivative.py' )
        eprint( '       -h, --help' )
        eprint( '       -d <x,y,xy>, --dir=<x,y,xy>' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None
 
        try:                                
            opts, args = getopt.getopt( argv, 
                                    'hp:d:', ['help','param=','dir='])
        except getopt.GetoptError as e:
            eprint( 'derivative: ' + str(e) )
            self.usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
                
            if opt in ( '-d', '--dir' ):
                
                ddir = arg
                if ddir not in ('x', 'X', 'y', 'Y', 'xy', 'XY' ):
                    self.usage()
                    sys.exit( 2 )

                if ddir in ('x','X' ):
                    self.p.ddir = 'x'
                
                elif ddir in ('y','Y' ):
                    self.p.ddir = 'y'
                
                elif ddir in ('xy','XY' ):
                    self.p.ddir = 'xy'

            elif opt in ( '-p', '--params' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'derivative: cannot find file:', arg,' ...exiting' )
                    sys.exit( 2 )
                params = arg

        if params != None:
            
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'derivative: set_params: bad params file read' )
                sys.exit( 2 )          
 
####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':

    oper = instantiate()      
    oper.set_params( sys.argv[1:] )

    import tempfile

    # numpy needs to 'seek' on the file to load
    # so read from stdin to temporary file
    
    temp_name = next( tempfile._get_candidate_names() ) + '.tmp'
    temp = open( temp_name, 'wb' )
    temp.write( sys.stdin.buffer.read() )
    temp.close()

    try:
        # load the numpy array data
        oper.source = np.load( temp_name, allow_pickle=True )
        oper.run()                  

        oper.sink.dump( sys.stdout.buffer )
        
    except Exception as e:
        eprint( str(e) )
   
    os.remove( temp_name )
