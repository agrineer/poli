#! /usr/bin/env python

'''
@file thrsh_li.py
@author Scott L. Williams.
@package POLI
@brief skimage li thresholding
@LICENSE
# 
#  thresh.py Copyright (C) 2010-2026 Scott L. Williams.
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
Compute threshold value by Li’s iterative Minimum Cross Entropy method.

Returns:
    threshold : float applied towards image
    Upper threshold value. All pixels with an intensity higher than
    this value are assumed to be foreground.

'''

# embed copyright in binary
thrsh_li_copyright = 'thrsh_li.py Copyright (c) 2010-2026 Scott L. Williams released under GNU GPL V3.0'

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
    #eprint( 'thrsh_li: using non-graphics mode.' )

def get_name():
    return 'thrsh_li'

# return an instance of 'thresh' class 
def instantiate():	
    return thrsh_li()

class thrsh_li_parameters( pio ):
    
    def __init__( self ):        
        self.tolerance = None
        self.guess = None
        self.binary = False
 
    def print_params( self ):        
        eprint( '\nparameters for thrsh_li:' )
        eprint( '               tolerance =', self.tolerance )
        eprint( '                   guess =', self.guess )
        eprint( '                  binary =', self.binary )

# ----------------------------------------------------------------------------

class thrsh_li( operator ):
    
    def __init__( self ): # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = thrsh_li_parameters()

    def print_versions( self ):       
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    def run( self ):                     # override superclass run

        self.p.print_params()            # report parameters used when running
        self.print_versions()

        source = np.copy( self.source )
        source[ np.isnan(source) ] = 0

        t_li = skimage.filters.threshold_li( source )
        
        mask = source > t_li        # boolean mask
        
        if self.p.binary: # show binary image
            self.sink = mask
        else:
            self.sink = source * mask
      
    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):

        tolerance = self.t_tolerance.GetValue().strip()
        if tolerance == '' or tolerance in [ 'None', 'none', 'NONE']:
            tolerance = None
        else:
            tolerance = float( tolerance )
            if tolerance <= 0:
                eprint( 'thrsh_li: read_params_from_panel:' )
                eprint( '          tolerance cannot be < 0' )
                eprint( '          ...returning' )
                return False
            
        guess = self.t_guess.GetValue().strip()
        if guess == '' or guess in [ 'None', 'none', 'NONE']:
            guess = None
        else:
            guess = float( tolerance )
            if guess <= 0:
                eprint( 'thrsh_li: read_params_from_panel:' )
                eprint( '          guess cannot be < 0' )
                eprint( '          ...returning' )
                return False
 
        self.p.binary = self.c_binary.GetValue()
        return True
    
    # write parameters to panel   
    def write_params_to_panel( self ):
        
        self.t_tolerance.SetValue( str( self.p.tolerance ) )
        self.t_guess.SetValue( str( self.p.guess ) )
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
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        # file input text control
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( p_fpanel, -1, '  tolerance:    ' )
        h_sizer.Add( prompt ) 
        
        self.t_tolerance = wx.TextCtrl( p_fpanel, -1,
                                        style=wx.ALIGN_RIGHT, size=(50,15) )
        self.t_tolerance.SetToolTip( 'Finish the computation when the change in the threshold in an iteration is less than this value. By default, this is half the smallest difference between intensity values in ' )
        h_sizer.Add( self.t_tolerance )
        v_sizer.Add( h_sizer )
        v_sizer.Add( 5, 5 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( p_fpanel, -1, '  guess:   ' )
        h_sizer.Add( prompt )
        h_sizer.Add( 25, 1 )
        self.t_guess = wx.TextCtrl( p_fpanel, -1,
                                    style=wx.ALIGN_RIGHT, size=(50,15) )
        self.t_guess.SetToolTip( 'An initial guess for the iteration can help the algorithm find the globally-optimal threshold' )
        h_sizer.Add( self.t_guess )
        v_sizer.Add( h_sizer )
        v_sizer.Add( 5, 5 )

        self.c_binary = wx.CheckBox( p_fpanel, 0, 'show binary' )
        v_sizer.Add( self.c_binary )
        p_fpanel.SetSizer( v_sizer )

        return p_fpanel
        
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: thrsh_li' )
        eprint( '       -h, --help' )
        eprint( '       -l value, --lower=value' )
        eprint( '       -u value, --upper=value' )
        eprint( '       -b, --binary' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hbt:g:p:', 
                                        ['help','binary','tolerance=',
                                         'guess=', 'params='] )
        except getopt.GetoptError as e:
           eprint( 'thrsh_li: ' + str(e) )  
           self.usage()                          
           sys.exit( 2 )  
 
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
                

            elif opt in ( '-b', '--binary' ):
                self.p.binary = True

            elif opt in ( '-t', '--tolerance' ):
                tol = float( arg )
                if tol < 0:
                    eprint( 'thrsh_li: tolerance value cannot be < 0' )
                    eprint( '          ...exiting' )
                    sys.exit( 2 )
                    
                self.p.tolerance = tol
                
            elif opt in ( '-g', '--guess' ):
                guess = float( arg )
                if guess < 0:
                    eprint( 'thrsh_li: guess value cannot be < 0' )
                    eprint( '          ...exiting' )
                    sys.exit( 2 )
  
                self.p.guess = guess

            elif opt in ( '-p', '--params' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'thrsh_li: cannot find parameter file:', arg,
                            ' ...exiting' )
                    sys.exit( 2 )
                params = arg
  
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'thrsh_li: set_params:' )
                eprint( '             bad params file read...exiting' )
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

