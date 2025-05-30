#! /usr/bin/env python3

'''
@file thrsh_local.py
@author Scott L. Williams.
@package POLI
@brief  skimage local thresholding
@LICENSE
#
#  thrsh_local.py Copyright (C) 2010-2025 Scott L. Williams.
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
Compute a threshold mask image based on local pixel neighborhood.

Also known as adaptive or dynamic thresholding. The threshold value is the
weighted mean for the local neighborhood of a pixel subtracted by a constant.

Alternatively the threshold can be determined dynamically by a given function,
using the ‘generic’ method.

Returns:
    threshold : (M, N[, …]) ndarray

        Threshold image. All pixels in the input image higher than the
        corresponding pixel in the threshold image are considered foreground.
'''

thrsh_local_copyright = 'thrsh_local.py Copyright (c) 2010-2025 Scott L. Williams, released under GNU GPL V3.0'

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
    eprint( 'thrsh_local: using non-graphics mode.' )

def get_name():
    return 'thrsh_local'

# return an instance of 'thresh-local' class 
def instantiate():	
    return thrsh_local( get_name() )

class thrsh_local_parameters( pio ):
    
    def __init__( self ):
        
        self.binary = False
        self.blocksize = 35        # must be odd
        self.offset = 0.0
        self.method ='gaussian'    # options: gaussian, mean, median
        self.mode = 'reflect'      # options: reflect, constant, nearest, wrap
        
    def print_params( self ):
        
        eprint( '\nparameters for thrsh_local:' )
        eprint( '    binary    =', self.binary )
        eprint( '    blocksize =', self.blocksize )
        eprint( '    offset    =', self.offset )
        eprint( '    method    =', self.method )
        eprint( '    mode      =', self.mode )
        
# ----------------------------------------------------------------------------

class thrsh_local( operator ):
    
    def __init__( self, name ):         # initialize op_panel but no graphics

        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = thrsh_local_parameters()
        
    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy   =', np.version.version )
        eprint( '   skimage =', skimage.__version__)

    def run( self ):
        
        self.p.print_params()           # report parameters used
        self.print_versions()

        t_local = skimage.filters.threshold_local( self.source,
                                                   self.p.blocksize,
                                                   method=self.p.method,
                                                   offset=self.p.offset,
                                                   mode=self.p.mode )
        
        mask = self.source > t_local     # boolean mask
        
        if self.p.binary:                # show binary image
            self.sink = mask
        else:
            self.sink = self.source * mask
      
    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):

        size = int( self.t_blocksize.GetValue().strip() )
        if size <= 0:
            eprint( 'thrsh_local: read_params_from_panel:' )
            eprint( '             blocksize must be positive and odd' )
            eprint( '             ...returning' )
            return
        
        if size % 2 == 0:
            eprint( 'thrsh_local: read_params_from_panel:' )
            eprint( '             blocksize must be odd')
            eprint( '             ...returning' )
            return

        offset = float( self.t_offset.GetValue().strip() )
        if offset < 0:
            eprint( 'thrsh_local: read_params_from_panel:' )
            eprint( '             offset cannot be < 0' )
            eprint( '             ...returning' )
            return False
        
        self.p.blocksize = size
        self.p.offset = offset          
        self.p.binary = self.c_binary.GetValue()
  
        # method
        if self.r_gauss.GetValue():
            self.p.method = 'gaussian'
            
        if self.r_mean.GetValue():
            self.p.method = 'mean'

        if self.r_median.GetValue():
            self.p.method = 'median'

        # mode
        if self.r_reflect.GetValue():
            self.p.mode = 'reflect'
            
        if self.r_constant.GetValue():
            self.p.mode = 'constant'
  
        if self.r_nearest.GetValue():
            self.p.mode = 'nearest'
            
        if self.r_mirror.GetValue():
            self.p.mode = 'mirror'

        if self.r_wrap.GetValue():
            self.p.mode = 'wrap'

        return True
    
    # write parameters to panel
    def write_params_to_panel( self ):

        self.c_binary.SetValue( self.p.binary )       
        self.t_blocksize.SetValue( str( self.p.blocksize ) )
        self.t_offset.SetValue( str( self.p.offset ) )

        # method
        if self.p.method == 'gaussian':
            self.r_gauss.SetValue( True )

        if self.p.method == 'mean':
            self.r_mean.SetValue( True )

        elif self.p.method == 'median':
            self.r_median.SetValue( True )

        # mode
        if self.p.mode == 'reflect':
            self.r_reflect.SetValue( True )

        if self.p.mode == 'constant':
            self.r_constant.SetValue( True )

        if self.p.mode == 'nearest':
            self.r_nearest.SetValue( True )
            
        if self.p.mode == 'mirror':
            self.r_mirror.SetValue( True )

        if self.p.mode == 'wrap':
            self.r_mirror.SetValue( True )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        panel = self.values_panel()
        h_sizer.Add( panel )
        h_sizer.Add( 10,1 )

        panel = self.method_panel()
        h_sizer.Add( panel )
        h_sizer.Add( 10,1 )

        panel = self.mode_panel()
        h_sizer.Add( panel )
        h_sizer.Add( 10,1 )
               
        self.p_client.SetSizer( h_sizer )
        self.write_params_to_panel()

    def values_panel( self ):

        p_values = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        prompt = wx.StaticText( p_values, -1, 'parms:' )
        v_sizer.Add( prompt )
        v_sizer.Add( 1,10 )

        self.c_binary = wx.CheckBox( p_values, 0, 'binary image' )
        v_sizer.Add( self.c_binary )
        v_sizer.Add( 1,10 )
 
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( p_values, -1, '    offset:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 30, 1 )

        self.t_offset = wx.TextCtrl( p_values, -1, '', size=(40,20),
                                     style=wx.ALIGN_RIGHT|wx.EXPAND )
        self.t_offset.SetToolTip( 'Constant subtracted from weighted mean of neighborhood to calculate the local threshold value. Default offset is 0' )
        h_sizer.Add( self.t_offset )
        h_sizer.Add( 10, 1 )
        v_sizer.Add( h_sizer )
        v_sizer.Add( 1,10 )
 
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( p_values, -1, '    block size:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 10, 1 )

        self.t_blocksize = wx.TextCtrl( p_values, -1, '', size=(40,20),
                                        style=wx.ALIGN_RIGHT )
        self.t_blocksize.SetToolTip( 'Odd size of pixel neighborhood which is used to calculate the threshold value (e.g. 3, 5, 7, …, 21, …)' )
        h_sizer.Add( self.t_blocksize )

        v_sizer.Add( h_sizer )
        p_values.SetSizer( v_sizer )
        return p_values

    def method_panel( self ):

        p_method = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )

        v_sizer = wx.BoxSizer( wx.VERTICAL )

        prompt = wx.StaticText( p_method, -1, 'method:' )
        v_sizer.Add( prompt )
        v_sizer.Add( 1,10 )

        self.r_gauss = wx.RadioButton( p_method, -1, 'gaussian', 
                                       style=wx.RB_GROUP )
        v_sizer.Add( self.r_gauss )
        v_sizer.Add( 1, 10 )

        self.r_mean = wx.RadioButton( p_method, -1, 'mean' )
        v_sizer.Add( self.r_mean )
        v_sizer.Add( 1, 10 )

        self.r_median = wx.RadioButton( p_method, -1, 'median' )
        v_sizer.Add( self.r_median )

        p_method.SetSizer( v_sizer )
        return p_method

    def mode_panel( self ):
        
        p_mode = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        
        prompt = wx.StaticText( p_mode, -1, 'mode:' )
        v_sizer.Add( prompt )
        v_sizer.Add( 1,10 )

        self.r_reflect = wx.RadioButton( p_mode, -1, 'reflect', 
                                         style=wx.RB_GROUP )
        v_sizer.Add( self.r_reflect )
 
        self.r_constant = wx.RadioButton( p_mode, -1, 'constant' )
        v_sizer.Add( self.r_constant )
 
        self.r_nearest = wx.RadioButton( p_mode, -1, 'nearest' )
        v_sizer.Add( self.r_nearest )
 
        self.r_mirror = wx.RadioButton( p_mode, -1, 'mirror' )
        v_sizer.Add( self.r_mirror )
        #v_sizer.Add( 1, 10 )

        self.r_wrap = wx.RadioButton( p_mode, -1, 'wrap' )
        v_sizer.Add( self.r_wrap )
        #v_sizer.Add( 1, 10 )

        p_mode.SetSizer( v_sizer )
        return p_mode

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        eprint('usage: thrsh_local' )
        eprint('       -h, --help' )
        eprint('       -b, --binary ' )
        eprint('             for binary output 0/255 ')
        eprint('       -s size, --size=size' )
        eprint('                  blocksize must be odd and positive' )
        eprint('       -o offset. --offset=offset' )
        eprint('       -m method, --method=method' )
        eprint('                  options: gaussian, mean, median' )
        eprint('       -d mode, --mode=mode' )
        eprint('                  options: reflect, constant, nearest, wrap' )
        eprint('       -p paramfile, --params=paramfile' )
        eprint('param file overrides line arguments' )
        eprint('input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hbs:o:m:d:p:', 
                                        ['help','binary',
                                         'size=','offset=','method=','mode=',
                                         'params=' ])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:   
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)
                
            elif opt in ( '-b', '--binary' ):
                self.p.binary = True

            elif opt in ( '-s', '--size' ):
                size = int( arg )
                
                if size <= 0:
                    eprint( 'thrsh_local: size must be > 0 ...exiting' )
                    sys.exit( 2 )
                    
                if size%2 == 0:
                    eprint( 'thrsh_local: size must be odd ...exiting' )
                    sys.exit( 2 )

                self.p.blocksize = size
 
            elif opt in ( '-o', '--offset' ):
                
                offset = int( arg )
                if offset < 0:
                    eprint( 'thrsh_local: offset must be > 0 ... exiting' )
                    sys.exit( 2 )
                    
                self.p.offset = offset
                
            elif opt in ( '-m', '--method' ):
                
                if arg not in ['gaussian', 'mean', 'median']:
                    eprint( 'thrsh_local: method must be one of:' )
                    eprint( '             gaussian, mean, or median' )
                    eprint( '             ...exiting')
                    sys.exit( 2 )
                            
                self.p.method = arg
                
            elif opt in ( '-d', '--mode' ):
                
                if arg not in ['reflect', 'constant', 'nearest', 'wrap']:
                    eprint( 'thrsh_local: mode must be one of:' )
                    eprint( '             reflect, constant, nearest, wrap' )
                    eprint( '             ...exiting')
                    sys.exit( 2 )
                            
                self.p.mode = arg
 
            elif opt in ( '-p', '--params' ):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'thrsh_local: cannot read parm file:', params,
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
        eprint( str(e) )
 
    os.remove( temp_name )
