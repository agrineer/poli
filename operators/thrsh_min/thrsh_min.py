#! /usr/bin/env python

'''
@file thrsh_min.py
@author Scott L. Williams.
@package POLI
@brief  skimage minimum thresholding
@LICENSE
#
#  thrsh_min.py Copyright (C) 2010-2026 Scott L. Williams.
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
Threshold value based on minimum method.

Returns:
    threshold: float applied towards image

    Upper threshold value. All pixels with an intensity higher than
    this value are assumed to be foreground.
'''

thrsh_min_copyright = 'thrsh_min.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

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
    #eprint( 'thrsh_min: using non-graphics mode.' )

def get_name():
    return 'thrsh_min'

# return an instance of 'thresh-local' class 
def instantiate():	
    return thrsh_min()

class thrsh_min_parameters( pio ):
    
    def __init__( self ):        
        self.binary = False
        self.max_iter = 10000
       
    def print_params( self ):       
        eprint( '\nparameters for thrsh_min:' )
        eprint( '                   binary =', self.binary )
        eprint( '           max iterations =', self.max_iter )
        
# ----------------------------------------------------------------------------

class thrsh_min( operator ):
    
    def __init__( self ):         # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = thrsh_min_parameters()
        
    def print_versions( self ):        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy   =', np.version.version )
        eprint( '   skimage =', skimage.__version__)

    def run( self ):

        self.p.print_params()           # report parameters used
        self.print_versions()

        t_min = skimage.filters.threshold_minimum( self.source,
                                                   max_num_iter=self.p.max_iter)
        
        mask = self.source > t_min     # boolean mask

        if self.p.binary: # show binary image
            self.sink = mask
        else:
            self.sink = self.source * mask
      
    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):

        max_iter = int( self.t_max_iter.GetValue().strip() )
        if max_iter <= 0:
            eprint( 'thrsh_min: read_params_from_panel:' )
            eprint( '           max iterations must be positive' )
            eprint( '           ...returning' )
            return False
        
        self.p.max_iter = max_iter
        self.p.binary = self.c_binary.GetValue()
 
        return True
    
    # write parameters to panel
    def write_params_to_panel( self ):

        self.c_binary.SetValue( self.p.binary )
        self.t_max_iter.SetValue( str(self.p.max_iter) )
 
    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1, 10 )
        self.c_binary = wx.CheckBox( self.p_client, 0, 'binary image' )
        v_sizer.Add( self.c_binary )
        v_sizer.Add( 1,10 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( self.p_client, -1, '    max iterations:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 10, 1 )

        self.t_max_iter = wx.TextCtrl( self.p_client, -1, '', size=(60,20),
                                     style=wx.ALIGN_RIGHT|wx.EXPAND )
        self.t_max_iter.SetToolTip( 'Maximum number of iterations to smooth the histogram.' )
        h_sizer.Add( self.t_max_iter )
        h_sizer.Add( 10, 1 )
        v_sizer.Add( h_sizer )
 
        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        eprint('usage: thrsh_min' )
        eprint('       -h, --help' )
        eprint('       -b, --binary ' )
        eprint('             for binary output 0/255 ')
        eprint('       -m num_iterations, --max=num_iterations' )
        eprint('       -p paramfile, --params=paramfile' )
        eprint('param file overrides line arguments' )
        eprint('input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hbm:p:', 
                                        [ 'help','binary','max=','params=' ])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:   
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)
                
            elif opt in ( '-b', '--binary' ):
                self.p.binary = True

            elif opt in ( '-m', '--max' ):
                imax = int( arg )
                
                if imax <= 0:
                    eprint( 'thrsh_min: max iterations must be > 0 ...exiting' )
                    sys.exit( 2 )
                    
                self.p.max_iter = imax
 
            elif opt in ( '-p', '--params' ):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'thrsh_min: cannot read parm file:', params,
                        ' ...exiting' )
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
