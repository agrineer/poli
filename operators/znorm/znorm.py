#! /usr/bin/env python

'''
@file znorm.py
@author Scott L. Williams
@package POLI
@brief Normalize all bands to either -1 to 1 or 0 to 1.
@LICENSE
#
#  znorm.py Copyright (C) 2010-2026 Scott L. Williams.
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
Normalize all bands to either -1 to 1 or 0 to 1.
Optionally report scaling coefficients to file 
Optionally consider interlaced buffers for scaling
'''

znorm_copyright = 'znorm.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint

# determine if graphics (wxpython) can be enabled
try:
    import wx
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
# if not then assume non-graphics implementation
except:
    from op import op
    operator = op
    #eprint( 'norm: using non-graphics mode.' )

def get_name(): 
    return 'znorm'

# return an instance of 'znorm' class 
def instantiate():	
    return znorm()

class znorm_parameters( pio ):              # hold arguments values here
    
    def __init__( self ):        
        self.ntype = 0                # 0 for 0 to 1; -1 for -1 to 1
        self.scope = 'pixel'          # options are: 'pixel' or 'all'

    def print_params( self ):        
        eprint( '\nparameters for znorm:' )
        eprint( '               ntype =', self.ntype )
        eprint( '               scope =', self.scope )
       
# ---------------------------------------------------------------------------

class znorm( operator ):
    
    def __init__( self ):       # initialize op_panel but no graphics
        
        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = znorm_parameters()
        
        self.cfile = None

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '   ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
        eprint( ' python  =', sys.version[0:6])

    def calc_coefficients( self, image, floor, ceiling ):

        # workaround for bug in nanmin wrt unsigned ints
        if image.dtype == np.uint8  \
        or image.dtype == np.uint16 \
        or image.dtype == np.uint32:
            imin = np.min( image )
            imax = np.max( image )
        else:
            imin = np.nanmin( image )         # get values to scale by
            imax = np.nanmax( image )         # ignoring nan

        if imax == imin :                # check for constant values
            scale = 0.0 	         # make image a surface plane
            c = 0.0
   
        elif np.isinf( imin ) or np.isinf( imax ):
            scale = 0.0 	         # make image a surface plane
            c = 0.0

        else:
            scale = (ceiling-floor)/float((imax-imin)) 
            c = floor-scale*imin

        return scale,c
    
    def run( self ):

        self.p.print_params()   # report parameters used when running
        self.print_versions()

        '''
        minval = np.min( self.source )
        maxval = np.max( self.source )
        self.sink = (data - minval) / (maxval - minval)
        '''

        if self.p.scope == 'all':
            
            scale, c = self.calc_coefficients( self.source, self.p.ntype, 1.0 )
            self.sink = self.source*scale + c
        else:
            # for every pixel
            ny,nx,nbands = self.source.shape
            self.sink = np.empty( (ny,nx,nbands), dtype=np.float32)
                
            for j in range( ny ):
                for i in range( nx ):
                    
                    scale, c = self.calc_coefficients( self.source[j,i,:], self.p.ntype, 1.0 )
                    self.sink[j,i,:] = self.source[j,i,:]*scale + c
        
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):     # scan panel parameters

       # normalization type
        if self.r_positive.GetValue():
            self.p.ntype = 0
        else:
            self.p.ntype = -1

        if self.r_pixel.GetValue():
            self.p.scope = 'pixel'
        else:
            self.p.scope = 'all'
 
        return True
     
    def write_params_to_panel( self ):       # write parameters to panel
        
        # normalization type
        if self.p.ntype == 0:
            self.r_positive.SetValue( True )
        else:
            self.r_negative.SetValue( True )

        if self.p.scope == 'all':
            self.r_all.SetValue( True )
        else:
            self.r_pixel.SetValue( True )
             
    # initialize panel graphics
    def init_panel( self, benchtop ):

        # FIXME: needs better layout format
        operator.init_panel( self, benchtop ) # start with basics

        # make parameter input boxes
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        
        panel = self.type_panel()
        v_sizer.Add( panel, 0, wx.ALL, 1 )
 
        panel = self.scope_panel()
        v_sizer.Add( panel, 0, wx.ALL, 1 )

        self.p_client.SetSizer( v_sizer )

        # populate with default values
        self.write_params_to_panel()

    def type_panel( self ):

        p_type = wx.Panel( self.p_client, -1 ) #, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 3, 2, 1, 1 )
        prompt = wx.StaticText( p_type, -1, 'normalize type:' )
        sizer.Add( prompt )
        sizer.Add( (1,1) )

        self.r_positive = wx.RadioButton( p_type, -1, '0 to 1', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_positive )
 
        self.r_negative = wx.RadioButton( p_type, -1, '-1 to 1' )
        sizer.Add( self.r_negative )
        
        p_type.SetSizer( sizer )
        
        return p_type

    def scope_panel( self ):

        p_type = wx.Panel( self.p_client, -1 ) #, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 3, 2, 1, 1 )
        prompt = wx.StaticText( p_type, -1, 'scope type:' )
        sizer.Add( prompt )
        sizer.Add( (1,1) )

        self.r_pixel = wx.RadioButton( p_type, -1, 'per pixel', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_pixel )
 
        self.r_all = wx.RadioButton( p_type, -1, 'all pixels' )
        sizer.Add( self.r_all )
        
        p_type.SetSizer( sizer )
        
        return p_type

    ############################################################
    # command line options for batch implementation
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: norm.py' )
        eprint( '       -h, --help' )
        eprint( '       -s [pixel,all]. --scope=[pixel,all]' )
        eprint( '       -t [0,-1], --type=[0,-1]' )
        eprint( '       -p param_file, --params=param_file' )
        eprint( '       input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None
        
        try:                                
            opts, args = getopt.getopt( argv, 'hs:t:p:',
                                        ['help','scope=','type=', 'param='] )
            
        except getopt.GetoptError as e:
            eprint( 'norm: '+ str(e) )
            self.usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            if opt in ( '-s', '--scope' ):
                if arg in ( 'pixel', 'PIXEL', 'p', 'all', 'ALL', 'a' ):
                    self.p.scope = arg
                else:
                    eprint( 'znorm: scope argument is bad: got ' + arg )
                    sys.exit( 2 )
                    
            if opt in ( '-t', '--type' ):
                 
                if arg in ('-1','0' ):
                    self.p.ntype = int( arg )
                else:
                    eprint( 'znorm: unknown type:', arg,
                            'must be -1 or 0 ...exiting' )
                    sys.exit( 2 )
                              
            if opt in ('-p', '--params'):
                params = arg

        # over rides other parameters
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( "znorm: cannot read parameter file" )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':

    try:
        import tempfile

        # read from stdin to temporary file
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
