#! /usr/bin/env python

'''
@file thrsh_notch.py
@author Scott L. Williams.
@package POLI
@brief single buffer notch thresholding
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
Threshold notch operator where lower and upper values define grey levels pass
through.

Returns notched image
'''

# embed copyright in binary
thrsh_notch_copyright = 'thrsh_notch.py Copyright (c) 2010-2026 Scott L. Williams released under GNU GPL V3.0'

import os
import sys
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
    #eprint( 'thrsh_notch: using non-graphics mode.' )

def get_name():
    return 'thrsh_notch'

# return an instance of 'thrsh_notch' class 
def instantiate():	
    return thrsh_notch()

class thrsh_notch_parameters( pio ):
    
    def __init__( self ):       
        self.lower = 64
        self.upper = 192
        self.binary = False
 
    def print_params( self ):       
        eprint( '\nparameters for thrsh_notch:' )
        eprint( '                      lower =', self.lower )
        eprint( '                      upper =', self.upper )
        eprint( '                     binary =', self.binary )

# ----------------------------------------------------------------------------

class thrsh_notch( operator ):
    
    def __init__( self ): # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = thrsh_notch_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    def run( self ):                     # override superclass run

        self.p.print_params()            # report parameters used when running
        self.print_versions()
 
        height,width,nbands = self.source.shape

        if nbands > 1 :
            eprint( 'thrsh_notch: not able to process multiband images' )
            return None

        if self.p.lower > self.p.upper:
            eprint( 'thrsh_notch: lower bound greater than upper bound' )
            return None

        source = np.copy( self.source )
        source[ np.isnan(source) ] = 0

        # make mask
        lmask = source >= self.p.lower
        hmask = source <= self.p.upper
        mask = lmask & hmask

        if self.p.binary: # show binary image
            self.sink = mask
        else:
            self.sink = source * mask

    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):
        
        lower = float( self.t_lower.GetValue().strip() )
        if lower < 0:
            eprint( 'thrsh_notch: read_params_from_panel:' )
            eprint( '         lower thresh value cannot be < 0' )
            eprint( '         ...returning' )
            return False
        
        upper = float( self.t_upper.GetValue().strip() )
        if upper < 0:
            eprint( 'thrsh_notch: read_params_from_panel:' )
            eprint( '         upper thresh value cannot be < 0' )
            eprint( '         ...returning' )
            return False
        
        if upper < lower:
            eprint( 'thrsh_notch: read_params_from_panel:' )
            eprint( '         upper thresh cannot be <  lower thresh' )
            eprint( '         ...returning' )
            return False
        
        self.p.lower = lower
        self.p.upper = upper
        self.p.binary = self.c_binary.GetValue()
 
        return True
    
    # write parameters to panel   
    def write_params_to_panel( self ):
        self.t_lower.SetValue( str( self.p.lower ) )
        self.t_upper.SetValue( str( self.p.upper ) )
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
        prompt = wx.StaticText( p_fpanel, -1, '  lower data value:    ' )
        h_sizer.Add( prompt )  # prompt
        
        self.t_lower = wx.TextCtrl( p_fpanel, -1,
                                    style=wx.ALIGN_RIGHT, size=(50,15) )
        self.t_lower.SetToolTip( '  lower bound to include' )
        h_sizer.Add( self.t_lower )
        v_sizer.Add( h_sizer )
        v_sizer.Add( 5, 5 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( p_fpanel, -1, '  upper data value:   ' )
        h_sizer.Add( prompt )   # prompt
        self.t_upper = wx.TextCtrl( p_fpanel, -1,
                                    style=wx.ALIGN_RIGHT, size=(50,15) )
        self.t_upper.SetToolTip( '  upper bound to include' )
        h_sizer.Add( self.t_upper )
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
        
        eprint( '\nusage: thrsh_notch' )
        eprint( '       -h, --help' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( '       -l value, --lower=value' )
        eprint( '       -u value, --upper=value' )
        eprint( '       -b, --binary' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hbp:l:u:', 
                                        ['help','binary','params=',
                                         'lower=','upper='] )
        except getopt.GetoptError as e:
           eprint( 'thrsh_notch: ' + str(e) )  
           self.usage()                          
           sys.exit( 2 )  
 
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
                
            if opt in ( '-p', '--params' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'thrsh_notch: cannot find parameter file:', arg,
                            ' ...exiting' )
                    sys.exit( 2 )
                params = arg
               
            elif opt in ( '-l', '--lower' ):
                self.p.lower = float( arg )
                
            elif opt in ( '-u', '--upper' ):               
                self.p.upper = float( arg )

            elif opt in ( '-b', '--binary' ):
                self.p.binary = True
                 
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'thrsh_notch: set_params:' )
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
