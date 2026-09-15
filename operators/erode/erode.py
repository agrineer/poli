#! /usr/bin/env python

'''
@file erode.py
@author Scott L. Williams.
@package POLI
@brief morphology erode operator
@LICENSE
#
#  erode.py Copyright (C) 2010-2026 Scott L. Williams.
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
erode_copyright = 'erode.py Copyright (c) 2010-2026 Scott L. Williams ' + \
                  'released under GNU GPL V3.0'

# morphology erode operator

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
    #eprint( 'erode: using non-graphics mode.' )

def get_name():
    return 'erode'

# return an instance of 'erode' class 
def instantiate():	
    return erode()

class erode_parameters( pio ):
    
    def __init__( self ):
        self.size = 2

    def print_params( self ):
        eprint( '\nparameters for erode:' )
        eprint( '                 size =', self.size )

# ----------------------------------------------------------------------------

class erode( operator ):
    
    def __init__( self ): # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )

        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = erode_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
        eprint( '   scipy =', scipy.version.version )

    def run( self ):            # override superclass run

        self.p.print_params()   # report parameters
        self.p.print_params()
        
        height,width,nbands = self.source.shape
        self.sink = scipy.ndimage.morphology.grey_erosion( self.source,
                                                           (self.p.size,
                                                           self.p.size,1) )

    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):
        
        size = int( self.t_size.GetValue().strip() )
        if size <= 0:
            eprint( 'erode: read_params_from_panel:' )
            eprint( '       size must be > 0' )
            eprint( '       ...returning' )
            return False
        
        self.p.size = size
        return True
 
    # write parameters to panel
    def write_params_to_panel( self ):
        self.t_size.SetValue( str(self.p.size) )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )

        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 
                                'enter influence size:' )

        v_sizer.Add( prompt, 0, wx.TOP, 8 )  # prompt

        self.t_size = wx.TextCtrl( self.p_client, -1,
                                    style=wx.ALIGN_RIGHT )
        self.t_size.SetToolTipString( 'enter influence size in pixels' )
        v_sizer.Add( self.t_size, 1)

        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()
    
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: erode.py' )
        eprint( '       -h, --help' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( '       -s size, --size=size' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hp:s:', ['help','param=','size='])
        except getopt.GetoptError as e:
            eprint( 'erode: ' + str(e) )
            usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                usage()                     
                sys.exit( 0 )
                
            if opt in ( '-p', '--params' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'erode: cannot find parameter file:', arg,
                            ' ...exiting' )
                    sys.exit( 2 )
                params = arg
                
            elif opt in ( '-s', '--size' ):
                
                if int(arg) <= 0:
                    eprint( 'erode: size must be > 0...exiting' )
                    sys.exit( 1 )        
                self.p.size = int( arg )

        if params != None:
            
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'erode: set_params: bad params file read...exiting' )
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

