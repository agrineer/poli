#! /usr/bin/env python

'''
@file equalhist.py
@author Scott L. Williams.
@package POLI
@brief equal histogram operator
@LICENSE
#
#  equalhis.py Copyright (C) 2010-2026 Scott L. Williams.
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
'''
equalhist_copyright = 'equalhis.py Copyright (c) 2010-2026 Scott L. Williams ' +\
                     'released under GNU GPL V3.0'

# equal histogram operator

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
    eprint( 'equalhis: using non-graphics mode.' ) 

def get_name(): 
    return 'equalhis'

# return an instance of 'equalhis' class 
def instantiate():	
    return equalhis()

class equalhis_parameters( pio ):       # hold arguments values here
    
    def __init__( self ):
        self.nbins = 255                # number of bins to use

    def print_params( self ):
        
        eprint( '\nparameters for equalhis:' )
        eprint( '                   nbins =', self.nbins )
         
# ----------------------------------------------------------------------------

class equalhis( operator ):
    
    def __init__( self ):      # initialize op_panel but no graphics
        
        name = os.path.basename(__file__)
        operator.__init__( self, name )       
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = equalhis_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    def run( self ):                 # override superclass run

        self.p.print_params()        # repeot parameters
        self.print_versions()
        
        height,width,nbands = self.source.shape
        self.sink = np.empty( self.source.shape,self.source.dtype)     

        # equalize probabilities for each band
        for i in range( nbands ):

            buf = self.source[:,:,i].flatten()
            hist,bins = np.histogram( buf, self.p.nbins )# normed=True )

            # adapted from Jan Solem's blog
            cdf = hist.cumsum()                     # cumulative distrib functn
            cdf = (buf.max()-buf.min())*cdf/cdf[-1] # normalize

            # interpolate new pixel values
            ebuf = np.interp( buf, bins[:-1], cdf ) + buf.min() 
            self.sink[:,:,i] = ebuf.reshape((height,width))

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        
        nbins = int( self.t_nbins.GetValue().strip() )
        if nbins <= 0:
            eprint( 'equalhis: read_params_from_panel:' )
            eprint( '          number of bins must be > 1' )
            eprint( '          ...returning' )
            return False
        
        self.p.nbins = nbins
        return True
    
    def write_params_to_panel( self ):   # write parameters to panel
        nbins = str( self.p.nbins )
        self.t_nbins.SetValue( nbins )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL)

        # number of bins
        h_sizer = wx.BoxSizer( wx.HORIZONTAL)
        prompt = wx.StaticText( self.p_client, -1, 'number of bins:' )
        h_sizer.Add( prompt, 0, wx.ALL, 6 )

        self.t_nbins = wx.TextCtrl( self.p_client, -1, '' )
        self.t_nbins.SetToolTip( 'enter number of bins' )
        h_sizer.Add( self.t_nbins, 0, wx.ALL, 1 )
        v_sizer.Add( h_sizer, 0 ,wx.ALL, 1 ) 
        self.p_client.SetSizer( v_sizer )

        self.write_params_to_panel()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: equalhis.py' )
        eprint( '       -h, --help' )
        eprint( '       -n nbins, --numbins=nbins' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hp:n:', 
                                        ['help','param=','numbins='])
        except getopt.GetoptError as e:
            eprint( 'equalhis: ' + str(e) )
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
                
            if opt in ( '-n', '--numbins' ):
                
                if int(arg) <= 0:
                    eprint( 'equalhis: number of bins must be > 0 ...exiting' )
                    sys.exit( 1 )                 
                self.p.nbins = int( arg )
                
            elif opt in ( '-p', '--params' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'equalhis: cannot find parameter file:', arg,
                            ' ...exiting' )
                    sys.exit( 2 )
                params = arg
  
        if params != None:
            
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'equalhis: set_params: bad params file read...exiting' )
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
