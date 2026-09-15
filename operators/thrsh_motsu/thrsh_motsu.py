#! /usr/bin/env python

'''
@file thrsh_motsu.py
@author Scott L. Williams.
@package POLI
@brief  skimage multi otsu thresholding
@LICENSE
#
#  thrsh_motsu.py Copyright (C) 2010-2026 Scott L. Williams.
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
Generate classes-1 threshold values to divide gray levels in image,
following Otsu’s method for multiple classes.

The threshold values are chosen to maximize the total sum of pairwise variances
between the thresholded graylevel classes. See Skimage Notes for more details.

Returns:

    thresh: array applied towards image

    Array containing the threshold values for the desired classes.
'''

thrsh_motsu_copyright = 'thrsh_motsu.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

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
    #eprint( 'thrsh_motsu: using non-graphics mode.' )

def get_name():
    return 'thrsh_motsu'

# return an instance of 'thresh-local' class 
def instantiate():	
    return thrsh_motsu()

class thrsh_motsu_parameters( pio ):
    
    def __init__( self ):
        self.nclasses = 5
       
    def print_params( self ):       
        eprint( '\nparameters for thrsh_motsu:' )
        eprint( '          number of classes =', self.nclasses )
        
# ----------------------------------------------------------------------------

class thrsh_motsu( operator ):
    
    def __init__( self ):         # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = thrsh_motsu_parameters()
        
    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy   =', np.version.version )
        eprint( '   skimage =', skimage.__version__)

    def run( self ):

        self.p.print_params()           # report parameters used
        self.print_versions()

        height, width, nbands = self.source.shape
        self.sink = np.empty( (height,width,nbands), dtype=np.int64 )
        
        for b in range( 0, nbands ):
            
            t_motsu = skimage.filters.threshold_multiotsu( self.source[:,:,b],
                                                       classes=self.p.nclasses )

            self.sink[:,:,b] = np.digitize( self.source[:,:,b], bins=t_motsu )
  
    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):

        nclasses = int( self.t_nclasses.GetValue().strip() )
        if nclasses <= 0:
            eprint( 'thrsh_motsu: read_params_from_panel: ' )
            eprint( '             number of classes must be positive ' )
            eprint( '             ...try again' )
            return False
        
        self.p.nclasses = nclasses
        return True

    # write parameters to panel
    def write_params_to_panel( self ):
       self.t_nclasses.SetValue( str(self.p.nclasses) )
 
    # initialize graphics
    def init_panel( self, benchtop ):

        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1, 10 )
        
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( self.p_client, -1, '    num classes:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 10, 1 )

        self.t_nclasses = wx.TextCtrl( self.p_client, -1, '', size=(30,20),
                                     style=wx.ALIGN_RIGHT|wx.EXPAND )
        self.t_nclasses.SetToolTip( 'Number of classes to be thresholded, i.e. the number of resulting regions' )
        h_sizer.Add( self.t_nclasses )
        h_sizer.Add( 10, 1 )
        v_sizer.Add( h_sizer )
 
        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        eprint('usage: thrsh_motsu' )
        eprint('       -h, --help' )
        eprint('       -n nclasses, --nclasses=nclasses' )
        eprint('       -p paramfile, --params=paramfile' )
        eprint('param file overrides line arguments' )
        eprint('input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hn:p:', 
                                        [ 'help','nclasses','params=' ])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:   
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)
                
            elif opt in ( '-n', '--classes' ):
                nclasses = int( arg )
                
                if nclasses <= 0:
                    eprint( 'thrsh_motsu: nclasses must be > 0 ...exiting' )
                    sys.exit( 2 )
                    
                self.p.nclasses = nclasses
 
            elif opt in ( '-p', '--params' ):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'thrsh_motsu: cannot read parm file:', params,
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
