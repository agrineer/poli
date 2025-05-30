#! /usr/bin/env python3

'''
@file thrsh_sauvola.py
@author Scott L. Williams.
@package POLI
@brief skimage sauvola thresholding
@LICENSE
# 
#  thresh.py Copyright (C) 2010-2025 Scott L. Williams.
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
Applies Sauvola local threshold to an array. Sauvola is a modification of Niblack technique.

In the original method a threshold T is calculated for every pixel in the image using the following formula:

T = m(x,y) * (1 + k * ((s(x,y) / R) - 1))

where m(x,y) and s(x,y) are the mean and standard deviation of pixel (x,y) neighborhood defined by a rectangular window with size w times w centered around the pixel. k is a configurable parameter that weights the effect of standard deviation. R is the maximum standard deviation of a grayscale image.

Returns:

    threshold : (M, N[, …]) ndarray applied towards image

    Threshold mask. All pixels with an intensity higher than this value are
    assumed to be foreground.
'''

# embed copyright in binary
thrsh_sauvola_copyright = 'thrsh_sauvola.py Copyright (c) 2010-2025 Scott L. Williams released under GNU GPL V3.0'

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
    eprint( 'thrsh_sauvola: using non-graphics mode.' )

def get_name():
    return 'thrsh_sauvola'

# return an instance of 'thresh' class 
def instantiate():	
    return thrsh_sauvola( get_name() )

class thrsh_sauvola_parameters( pio ):
    
    def __init__( self ):

        self.binary = False
        self.wsize = 15           # must be odd integer
        self.k = 0.2
        self.R = None             # the dynamic range of standard deviation
                                  # if None then R gets set to the half of the
                                  # dynamic range of the image type
  
    def print_params( self ):
        
        eprint( '\nparameters used for thrsh_sauvola:' )
        eprint( '    binary      =', self.binary )
        eprint( '    window size =', self.wsize)
        eprint( '    k           =', self.k )
        eprint( '    R           =', self.R )

# ----------------------------------------------------------------------------

class thrsh_sauvola( operator ):
    
    def __init__( self, name ): # initialize op_panel but no graphics
        
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = thrsh_sauvola_parameters()

    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    def run( self ):            

        self.p.print_params()            # report parameters used when running
        self.print_versions()

        # does not work; won't self.p.R == None
        t_niblack = skimage.filters.threshold_sauvola( self.source,
                                                       window_size=self.p.wsize,
                                                       k=self.p.k, r=self.p.R )
        # make mask
        mask = self.source > t_niblack

        if self.p.binary: # show binary image
            self.sink = mask
        else:
            self.sink = self.source * mask
        
    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):
        
        wsize = int( self.t_wsize.GetValue().strip() )
        if wsize < 0:
            eprint( 'thrsh_sauvola: read_params_from_panel:' )
            eprint( '               window size cannot be < 0' )
            eprint( '               ...returning' )
            return False
        
        if wsize % 2 == 0:
            eprint( 'thrsh_sauvola: read_params_from_panel:' )
            eprint( '               window size must be odd integer' )
            eprint( '               ...returning' )
            return False
           
        k = float( self.t_k.GetValue().strip() )
        if k < 0:
            eprint( 'thrsh_sauvola: read_params_from_panel:' )
            eprint( '               k cannot be < 0' )
            eprint( '               ...returning' )
            return False
        
        R = self.t_R.GetValue().strip()
        if R == '' or R in ['None','none', 'NONE']:
            R = None
            
        else:
            R = float( R )
            if R < 0:
                eprint( 'thrsh_sauvola: read_params_from_panel:' )
                eprint( '               R must be > 0' )
                eprint( '               ...returning' )
                return False
            
        self.p.wsize = wsize
        self.p.k = k
        self.p.R = R

        self.p.binary = self.c_binary.GetValue()
        return True
    
    # write parameters to panel   
    def write_params_to_panel( self ):
        
        self.t_wsize.SetValue( str( self.p.wsize ) )
        self.t_k.SetValue( str( self.p.k ) )

        if self.p.R == None or self.p.R == '':
            self.t_R.SetValue( 'None' )
        else:
            self.t_R.SetValue( str( self.p.R ) )
            
        self.c_binary.SetValue( self.p.binary )
  
    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        # lay out sizers for future panels
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        panel = self.first_panel()

        h_sizer.Add( panel )
        v_sizer.Add( h_sizer )

        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    def first_panel( self ):
        
        p_fpanel = wx.Panel( self.p_client, -1 )#, style=wx.SUNKEN_BORDER )
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1, 10 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( p_fpanel, -1, '  k:   ' )
        h_sizer.Add( prompt )   
        self.t_k = wx.TextCtrl( p_fpanel, -1,
                                style=wx.ALIGN_RIGHT, size=(50,15) )
        self.t_k.SetToolTip( 'Value of the positive parameter k' )
        h_sizer.Add( self.t_k )
        h_sizer.Add( 10, 1 )
        v_sizer.Add( h_sizer )
        v_sizer.Add( 1, 10 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( p_fpanel, -1, '  R:   ' )
        h_sizer.Add( prompt )   
        self.t_R = wx.TextCtrl( p_fpanel, -1,
                                style=wx.ALIGN_RIGHT, size=(50,15) )
        self.t_R.SetToolTip( 'Value of R, the dynamic range of standard deviation. If None, set to the half of the image dtype range' )
        h_sizer.Add( self.t_R )
        h_sizer.Add( 10, 1 )
        v_sizer.Add( h_sizer )
        v_sizer.Add( 1, 10 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( p_fpanel, -1, '  window size:    ' )
        h_sizer.Add( prompt )        
        self.t_wsize = wx.TextCtrl( p_fpanel, -1,
                                    style=wx.ALIGN_RIGHT, size=(30,20) )
        self.t_wsize.SetToolTip( 'Window size specified as a single odd integer (3, 5, 7, …), or an iterable of length image.ndim containing only odd integers (e.g. (1, 5, 5))' )
        h_sizer.Add( self.t_wsize )
        v_sizer.Add( h_sizer )
        v_sizer.Add( 1, 10 )

        self.c_binary = wx.CheckBox( p_fpanel, 0, 'show binary' )
        v_sizer.Add( self.c_binary )

        p_fpanel.SetSizer( v_sizer )

        return p_fpanel
        
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: thrsh_sauvola' )
        eprint( '       -h, --help' )
        eprint( '       -b, --binary' )
        eprint( '       -w value, --wsize=value' )
        eprint( '       -k value, --k=value' )
        eprint( '       -r value, --R=value' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hbw:k:r:p:', 
                                        ['help','binary','wsize=','k=','R=',
                                         'params='] )
        except getopt.GetoptError as e:
           eprint( 'thrsh_sauvola: ' + str(e) )  
           self.usage()                          
           sys.exit( 2 )  
 
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
                
            elif opt in ( '-b', '--binary' ):
                self.p.binary = True
                
            elif opt in ( '-w', '--wsize' ):
                wsize =  int( arg )
                if wsize < 1:
                    eprint( 'thrsh_sauvola: wsize cannot be < 1...exiting' )
                    sys.exit( 2 )
                self.p.wsize = wsize

            elif opt in ( '-k', '--k' ):
                # TODO: find parameters for k
                self.p.k = float( arg )

            elif opt in ( '-r', '--R' ):
                # TODO: find parameters for R
                self.p.R = float( arg )

            elif opt in ( '-p', '--params' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'thrsh_sauvola: set_params:' )
                    eprint( '               parameter file not found:',
                            arg, ' ...exiting' )
                    sys.exit( 2 )
                params = arg
   
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'thrsh_sauvola: cannot read parm file:', params,
                        ' ...exiting' )
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
