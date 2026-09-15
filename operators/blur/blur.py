#! /usr/bin/env python

'''
@file blur.py
@author Scott L. Williams.
@package POLI
@brief Gaussian or flat blur operator
@LICENSE
# 
#  blur.py Copyright (C) 2010-2026 Scott L. Williams.
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
neighborhood blurring with simple gaussian or flat kernels
'''

blur_copyright = 'blur.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

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
    #eprint( 'blur: using non-graphics mode.' )

def get_name():                
    return 'blur'

# return an instance of 'blur' class 
def instantiate():
    return blur()

class blur_parameters( pio ):        # hold arguments values here
    
    def __init__( self ):
        
        self.btype = 'gauss'    # types are flat, gauss
        self.times = 4          # how many times to blur image

    def print_params( self ):
        
        eprint( '\nparameters for blur:' )
        eprint( '                type =', self.btype )
        eprint( '               times =', self.times )
        
# ---------------------------------------------------------------------------

class blur( operator ):
    
    def __init__( self ): # initialize operator but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = blur_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
        eprint( '   scipy =', scipy.version.version )

    def run( self ):                     # override superclass run

        self.p.print_params()            # report parameters used when running
        self.print_versions()
        
        height,width,nbands = self.source.shape

        # make output float
        temp = np.empty( (height,width,nbands),
                              dtype=np.float32 )

        if self.p.btype == 'flat':
            kernel = np.array( [1.0, 1.0, 1.0,  # column vectors
                                1.0, 1.0, 1.0,
                                1.0, 1.0, 1.0 ] )
            kernel.shape = 3,3,1
            factor = 9

        elif self.p.btype == 'gauss':
            kernel = np.array( [1.0, 1.0, 1.0,  # column vectors
                                1.0, 5.0, 1.0,
                                1.0, 1.0, 1.0 ] )
            kernel.shape = 3,3,1
            factor = 13

        blur = self.source

        for i in range( 0, self.p.times ):
            scipy.ndimage.convolve( blur, kernel, output=temp )
            blur = temp/factor
            
        self.sink = blur

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):       # scan panel parameters

        times = int( self.t_times.GetValue().strip() )
        if times <= 0:
            eprint( 'blur: read_params_from_panel:' )
            eprint( '      times must be > 0' )
            eprint( '      ...returning' )
            return False
        
        self.p.times = times
 
        if self.r_flat.GetValue():
            self.p.btype = 'flat'           
        else:
            self.p.btype = 'gauss'
            
        return True

    def write_params_to_panel( self ):        # write parameters to panel
        
        if  self.p.btype == 'flat':
            self.r_flat.SetValue( True )           
        else:
            self.r_gauss.SetValue( True )
 
        self.t_times.SetValue( str( self.p.times ) )

    # initialize panels graphics
    def init_panel( self, benchtop ):

        operator.init_panel( self, benchtop ) # start with basics

        # lay out sizers for future panels
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        panel = self.btype_panel()

        h_sizer.Add( panel )
        v_sizer.Add( h_sizer )

        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    def btype_panel( self ):

        p_type = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
 
        self.r_flat = wx.RadioButton( p_type, -1, 'flat', style = wx.RB_GROUP )
        v_sizer.Add( self.r_flat )
        v_sizer.Add( (1,1) )

        self.r_gauss = wx.RadioButton( p_type, -1, 'gauss' )
        v_sizer.Add( self.r_gauss )
        v_sizer.Add( (1,1) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        prompt = wx.StaticText( p_type, -1, '  times:' )
        h_sizer.Add( prompt )
        self.t_times = wx.TextCtrl( p_type, -1, '', size=(40,20) )
        h_sizer.Add( self.t_times )

        v_sizer.Add( h_sizer )
        p_type.SetSizer( v_sizer )

        return p_type
        
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: blur.py' )
        eprint( '       -h, --help' )
        eprint( '       -t <flat,gauss>, --type=<flat,gauss>' )
        eprint( '       -n num of times, --num=num of times>' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 'ht:n:p:',
                                        ['help','type=','num=','params='])
        except getopt.GetoptError as e:
            eprint( 'blur: ' + str(e) )
            self.usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            if opt in ( '-t', '--type' ):
                
                if arg == 'flat':
                    self.p.btype = arg
                    
                elif arg == 'gauss':
                    self.p.btype = arg
                    
                else:
                    eprint( 'blur: bad type:', arg,
                            ' must be <flat or gauss> ...exiting' )
                    sys.exit( 2 )

            elif opt in ( '-n', '--num' ):
                
                if int(arg) <= 0:
                    eprint( 'blur: number of times must be > 0 ...exiting' )
                    sys.exit( 1 )        
                self.p.times = int( arg )

            elif opt in ( '-p', '--params' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'blur: cannot find file:', arg, ' ...exiting' )
                    sys.exit( 2 )
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
