#! /usr/bin/env python

'''
@file thrsh_iso.py
@author Scott L. Williams.
@package POLI
@brief skimage iso data thresholding
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

Histogram-based threshold, known as Ridler-Calvard method or inter-means. Threshold values returned satisfy the following equality:

threshold = (image[image <= threshold].mean() +
             image[image > threshold].mean()) / 2.0
Returns:

    threshold : float or int or array applied towards image
'''

# embed copyright in binary
thrsh_iso_copyright = 'thrsh_iso.py Copyright (c) 2010-2026 Scott L. Williams released under GNU GPL V3.0'

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
    #eprint( 'thrsh_iso: using non-graphics mode.' )

def get_name():
    return 'thrsh_iso'

# return an instance of 'thresh' class 
def instantiate():	
    return thrsh_iso()

class thrsh_iso_parameters( pio ):
    
    def __init__( self ):
        #self.nbins = None
        self.return_all = False
        self.binary = False
 
    def print_params( self ):
        eprint( '\nparameters for thrsh_iso:' )
        eprint( '               return_all =', self.return_all )
        eprint( '                   binary =', self.binary )

# ----------------------------------------------------------------------------

class thrsh_iso( operator ):
    
    def __init__( self ): # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = thrsh_iso_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
        eprint( '   skimage =', skimage.__version__)

    def run( self ):                     # override superclass run

        self.p.print_params()            # report parameters used when running
        self.print_versions()

        source = np.copy( self.source )
        source[ np.isnan(source) ] = 0
        t_iso = skimage.filters.threshold_isodata( source,
                                                   return_all=self.p.return_all )
        mask = source > t_iso        # boolean mask

        if self.p.binary:            # show binary image
            self.sink = mask
        else:
            self.sink = source * mask

    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):

        self.p.return_all = self.c_return_all.GetValue()
        self.p.binary = self.c_binary.GetValue()
        return True
    
    # write parameters to panel   
    def write_params_to_panel( self ):
        
        self.c_return_all.SetValue( self.p.return_all )
        self.c_binary.SetValue( self.p.binary )
 
    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        # lay out sizers for future panels
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1, 10 )

        self.c_binary = wx.CheckBox( self.p_client, 0, '   show binary' )
        v_sizer.Add( self.c_binary )
        v_sizer.Add( 1, 10 )

        self.c_return_all = wx.CheckBox( self.p_client, 0, '   return all' )
        self.c_return_all.SetToolTip( 'If False (default), return only the lowest threshold that satisfies the above equality. If True, return all valid thresholds.' )
        v_sizer.Add( self.c_return_all )
 
        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()
      
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: thrsh_iso' )
        eprint( '       -h, --help' )
        eprint( '       -b, --binary' )
        eprint( '       -a, --all' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hba', 
                                        ['help','binary','all', 'params='] )
        except getopt.GetoptError as e:
           eprint( 'thrsh_iso: ' + str(e) )  
           self.usage()                          
           sys.exit( 2 )  
 
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            elif opt in ( '-b', '--binary' ):
                self.p.binary = True

            elif opt in ( '-a', '--all' ):
                self.p.return_all = True
 
            if opt in ( '-p', '--params' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'thrsh_iso: cannot find parameter file:', arg,
                            ' ...exiting' )
                    sys.exit( 2 )
                params = arg
                 
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'thrsh_iso: set_params:' )
                eprint( '           bad params file read...exiting' )
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
