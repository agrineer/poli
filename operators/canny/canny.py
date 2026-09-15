#! /usr/bin/env python
'''
@file canny.py
@author Scott L. Williams.
@package POLI
@brief canny edge detection operator
@LICENSE
#
#  canny.py Copyright (C) 2010-2026 Scott L. Williams.
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
From: scikit-image
canny edge detection operator for poli
The steps of the algorithm are as follows:

    Smooth the image using a Gaussian with sigma width.(SEE POLI gauss.py)

    Apply the horizontal and vertical Sobel operators to get the gradients
    within the image. The edge strength is the norm of the gradient.

    Thin potential edges to 1-pixel wide curves. First, find the normal to
    the edge at each point. This is done by looking at the signs and the
    relative magnitude of the X-Sobel and Y-Sobel to sort the points into
    4 categories: horizontal, vertical, diagonal and antidiagonal. Then look
    in the normal and reverse directions to see if the values in either of
    those directions are greater than the point in question. Use interpolation
    to get a mix of points instead of picking the one that’s the closest to
    the normal.

    Perform a hysteresis thresholding: first label all points above the high
    threshold as edges. Then recursively label any point above the low
    threshold that is 8-connected to a labeled point as an edge.
'''

canny_copyright = 'canny.py Copyright (c) 2010-2026 Scott L. Williams ' + \
                  'released under GNU GPL V3.0'

#
import os
import sys
import skimage
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
    #eprint( 'canny: using non-graphics mode.')

def get_name(): 
    return 'canny'

# return an instance of 'cannyedge' class 
def instantiate():	
    return canny()

class canny_parameters( pio ):  # hold arguments values here
    
    def __init__( self ):
        
        self.sigma = 1.4        # standard deviation of the gaussian filter
        self.low_thresh = None  # if None low threshold is set to 10% dtype max 
        self.high_thresh = None # if None high threshold is set to 20% dtype max

        self.use_quantiles = False  # If True then treat low_threshold and
                                    # high_threshold as quantiles of the edge
                                    # magnitude image, rather than absolute
                                    # edge magnitude values. If True then the
                                    # thresholds must be in the range [0, 1]
                                    
        self.mode = 'reflect'   # The mode parameter determines how the array
                                # borders are handled during Gaussian filtering,
                                # where cval (below) is the value when mode 
                                # is equal to ‘constant’
                                
        self.cval = 0.0         # Value to fill past edges of input if mode
                                # is ‘constant’.

        self.boolean = False    # True sets outgoing buffer as boolean
        
    def print_params( self ):
        
        eprint( '\nparameters for canny:' )
        eprint( '                sigma =', self.sigma )
        eprint( '           low thresh =', self.low_thresh )
        eprint( '          high thresh =', self.high_thresh )
        eprint( '        use_quantiles =', self.use_quantiles )
        eprint( '                 mode =', self.mode )
        eprint( '                 cval =', self.cval )
        eprint( '       boolean output =', self.boolean )
 
# -------------------------------------------------------------------------

class canny( operator ):
    
    def __init__( self ):      # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = canny_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
        eprint( '   skimage =', skimage.__version__ )
  
    def run( self ):
        
        self.p.print_params()        # report parameters
        self.print_versions()
       
        self.sink = np.empty( self.source.shape, dtype=np.bool )     
        height,width,nbands = self.source.shape

        # for now, use the same canny parameters for each band
        for i in range( nbands ):      # edge detect for each band
 
            self.sink[:,:,i] = skimage.feature.canny( self.source[:,:,i], 
                                                      sigma=self.p.sigma,
                                         low_threshold=self.p.low_thresh,
                                       high_threshold=self.p.high_thresh,
                                      use_quantiles=self.p.use_quantiles,
                                                        mode=self.p.mode,
                                                        cval=self.p.cval )
        if not self.p.boolean:
            self.sink = (self.sink*255).astype( np.uint8 )
            
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        
        self.p.sigma = float( self.t_sigma.GetValue().strip() )

        value = self.t_low_thresh.GetValue().strip()
        if value == 'None':
            self.p.low_thresh = None
        else:
            self.p.low_thresh = float( value )

        value = self.t_high_thresh.GetValue().strip()
        if value == 'None':
            self.p.high_thresh = None
        else:
            self.p.high_thresh = float( value )

        value = self.t_cval.GetValue().strip()
        if value == 'None':
            self.p.cval = 0.0
        else:
            self.p.cval = float( value )
             
        self.p.use_quantiles = self.c_use_quantiles.GetValue()
        self.p.boolean = self.c_boolean.GetValue()
        
        if self.r_reflect.GetValue():           
            self.p.mode = 'reflect'
            
        elif self.r_constant.GetValue():
            self.p.mode = 'constant'

        elif self.r_nearest.GetValue():
            self.p.mode = 'nearest'

        elif self.r_mirror.GetValue():
            self.p.mode = 'mirror'

        elif self.r_wrap.GetValue():
            self.p.mode = 'wrap'

        else:
            eprint( 'canny:read_params_from_panel: unknown mode!!' )
            return False
        
        return True
        
    def write_params_to_panel( self ):   # write parameters to panel
        
        sigma = str( self.p.sigma )
        self.t_sigma.SetValue( sigma )
        
        tlow = str( self.p.low_thresh )
        self.t_low_thresh.SetValue( tlow )
        
        thigh = str( self.p.high_thresh )
        self.t_high_thresh.SetValue( thigh )

        cval = str( self.p.cval )
        self.t_cval.SetValue( cval )
        
        self.c_use_quantiles.SetValue( self.p.use_quantiles )
        self.c_boolean.SetValue( self.p.boolean )
        
        if self.p.mode == 'reflect':
            self.r_reflect.SetValue( True )

        elif self.p.mode == 'constant':
            self.r_constant.SetValue( True )

        elif self.p.mode == 'nearest':
            self.r_nearest.SetValue( True )

        elif self.p.mode == 'mirror':
            self.r_mirror.SetValue( True )

        elif self.p.mode == 'wrap':
            self.r_wrap.SetValue( True )
            
        else:
            eprint( 'canny: write_params_to_panel: unknown mode=', self.mode )
        
    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics
        
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        
        panel = self.values_panel()
        h_sizer.Add( panel )
        h_sizer.Add( 25, 1 )

        panel = self.radio_panel()
        h_sizer.Add( panel )
        h_sizer.Add( 25, 1 )

        panel = self.checkbox_panel()
        h_sizer.Add( panel )

        self.p_client.SetSizer( h_sizer )
        self.write_params_to_panel()

    def values_panel( self ):

        v_panel  = wx.Panel( self.p_client )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1, 10 )

        # sigma
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( v_panel, -1, ' sigma:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 43, 1 )

        self.t_sigma = wx.TextCtrl( v_panel, -1, '', size=(50,20) )
        self.t_sigma.SetToolTip( 'enter sigma value' )
        h_sizer.Add( self.t_sigma, 0, wx.ALL, 1 )
        v_sizer.Add( h_sizer, 0, wx.ALL, 1 ) 

        # low threshold
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( v_panel, -1, ' thresh low:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 16, 1 )

        self.t_low_thresh = wx.TextCtrl( v_panel, -1, '', size=(50,20) )
        self.t_low_thresh.SetToolTip( 'enter low threshold' )
        h_sizer.Add( self.t_low_thresh, 0, wx.ALL, 1 )
        v_sizer.Add( h_sizer, 0, wx.ALL, 1 ) 

        # high threshold
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( v_panel, -1, ' thresh high:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 11, 1 )

        self.t_high_thresh = wx.TextCtrl( v_panel, -1, '',size=(50,20) )
        self.t_high_thresh.SetToolTip( 'enter high threshold' )
        h_sizer.Add( self.t_high_thresh, 0, wx.ALL, 1 )
        v_sizer.Add( h_sizer, 0, wx.ALL, 1 ) 

        # constant value
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( v_panel, -1, ' const. value:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 11, 1 )

        self.t_cval = wx.TextCtrl( v_panel, -1, '',size=(50,20) )
        self.t_cval.SetToolTip( 'enter constant value when mode==constant' )
        h_sizer.Add( self.t_cval, 0, wx.ALL, 1 )
        v_sizer.Add( h_sizer ) 

        v_panel.SetSizer( v_sizer )
        return v_panel

    def checkbox_panel( self ):
        c_panel  = wx.Panel( self.p_client )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1, 10 )

        # use quantiles
        self.c_use_quantiles = wx.CheckBox( c_panel, 0, 'use quantiles')     
        v_sizer.Add( self.c_use_quantiles )
        v_sizer.Add( 1, 10 )
        
        # boolean output
        self.c_boolean = wx.CheckBox( c_panel, 0, 'boolean output')     
        v_sizer.Add( self.c_boolean )
        v_sizer.Add( 1, 10 )

        c_panel.SetSizer( v_sizer )
        return c_panel

    def radio_panel( self ):
        
        r_panel  = wx.Panel( self.p_client )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1, 10 )
 
        self.r_reflect = wx.RadioButton( r_panel, -1, 'reflect', 
                                          style = wx.RB_GROUP )
        v_sizer.Add( self.r_reflect )

        self.r_wrap = wx.RadioButton( r_panel, -1, 'wrap' )
        v_sizer.Add( self.r_wrap)
       
        self.r_nearest = wx.RadioButton( r_panel, -1, 'nearest' )
        v_sizer.Add( self.r_nearest )

        self.r_mirror = wx.RadioButton( r_panel, -1, 'mirror' )
        v_sizer.Add( self.r_mirror )
 
        self.r_constant = wx.RadioButton( r_panel, -1, 'constant' )
        v_sizer.Add( self.r_constant )
 
        r_panel.SetSizer( v_sizer )

        return r_panel
 
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( 'usage: canny.py' )
        eprint( '    -h, --help' )
        eprint( '    -b, --bool  for boolean type output' )
        eprint( '    -u, --use_quantiles' )
        eprint( '    -s sigma, --sigma=sigma' )
        eprint( '    -l low_thresh, --low=low_thresh' )
        eprint( '    -t top_thresh, --top=top_thresh' )
        eprint( '    -m mode, --mode=mode' )
        eprint( '       where mode is in (reflect,constant,nearest,mirror,wrap')
        eprint( '    -c cval, --cval-cval' )
        eprint( '        cval value is used when mod == constant' )
        eprint( '     p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hbus:l:t:m:c:p:', 
                                        ['help','bool', 'use_quantiles',
                                         'sigma=','low=','top=','mode=',
                                         'cval=', 'params='])
        except getopt.GetoptError:
            eprint( 'canny: ' + str(e) )   
            self.usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            if opt in ( 'b', '--bool' ):
                self.p.boolean = True
  
            if opt in ( 'u', '--use_quantiles' ):
                self.p.use_quantiles = True
                
            elif opt in ( '-s', '--sigma' ):
                farg = float(arg)
                if farg <= 0:
                    eprint( 'canny: sigma must be positive, got:', farg )
                    sys.exit( 2 )
                    
                self.p.sigma = float( arg )
                
            elif opt in ( '-l', '--low' ):
                farg = float( arg )
                if farg <= 0:
                    eprint( 'canny: low threshold  must be positive, got:',
                            farg )
                    sys.exit( 2 )                  
                self.p.low_thresh = farg
                
            elif opt in ( '-t', '--top' ):
                farg = float( arg )
                if farg <= 0:
                    eprint( 'canny: top threshold  must be positive, got:',
                            farg )
                    sys.exit( 2 )
                self.p.high_thresh = farg

            elif opt in ( 'm', '--mode' ):
                if arg in ('reflect','constant','nearest','mirror','wrap'):
                    self.p.mode = arg

            elif opt in ( 'c', --cval ):
                farg = float( arg )
                if farg <= 0:
                    eprint( 'canny: cval must be positive, got:', farg )
                    sys.exit( 2 )
                    
            elif opt in ('-p', '--params'):
                params = arg  

        '''
        if self.p.low_threshold >= self.p.high_threshold:
            eprint( 'canny: low_threshold is >= top_threshold...exiting' )
            sys.exit( 2 )
        '''
            
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( "canny: cannot read parameter file" )
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
