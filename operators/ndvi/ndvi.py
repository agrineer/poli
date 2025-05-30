#! /usr/bin/env python3

'''
@file ndvi.py
@author Scott L. Williams.
@package POLI
@brief normalized difference vegetation index 
@LICENSE

#  ndvi.py
# 
#  Copyright (C) 2010-2025 Scott L. Williams.
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
ndvi operator using red and nir bands
normalized difference vegetation index gives an estimate of live
vegetation biom

ndvi= (nir-red)/(nir+red)
'''

ndvi_copyright = 'ndvi.py Copyright (c) 2010-2025 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

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
    eprint( 'ndvi: using non-graphics mode.' )

def get_name(): 
    return 'ndvi'

# return an instance of 'ndvi' class 
def instantiate():	
    return ndvi( get_name() )

class ndvi_parameters( pio ):       # hold arguments values here
    
    def __init__( self ):
        self.red = 0                # bands to use AVHRR default
        self.nir = 1

    def print_params( self ):
        
        eprint( '\nparameters for ndvi:' )
        eprint( '    red band  =', self.red )
        eprint( '    nir band  =', self.nir )

class ndvi( operator ):
    
    def __init__( self, name ):      # initialize op_panel but no graphics
        operator.__init__( self, name )
        self.op_id = 'ndvi version 0.0'
        self.p = ndvi_parameters()
        
    def run( self ):                 # override superclass run      
        height,width,nbands = self.source.shape

        # check band range
        if  self.p.red < 0 or self.p.red >= nbands:
            eprint('ndvi: bad red band value=', self.p.red )
            self.sink = None
            return

        if  self.p.nir < 0 or self.p.nir >= nbands:
            eprint( 'ndvi: bad nir band value=', self.p.nir )
            self.sink = None
            return
 
        # make float
        red = self.source[:,:,self.p.red].astype( np.float32 )
        nir = self.source[:,:,self.p.nir].astype( np.float32 )
        
        numerator = nir - red    # subtract red from nir to get numerator
        denominator = nir + red  # add nir and red to get denominator

        self.sink = numerator/denominator
        self.sink.shape = height,width,1   # make 3-d 1-band

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        eprint( 'usage: ndvi.py' )
        eprint( '       -h, --help' )
        eprint( '       -r band, --red=band' )
        eprint( '       -n band, --nir=band' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hp:r:n:', 
                                        ['help','param=','red=','nir='])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit( 2)   
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
                
            elif opt in ( '-r', '--red' ):                
                self.p.red = int( arg )
                
            elif opt in ( '-n', '--nir' ):                
                self.p.nir = int( arg )
                
            elif opt in ('-p', '--params'):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                sys.exit( 2 )
                
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        
        red = int( self.t_rb.GetValue().strip() )
        if red < 0:
            eprint( 'ndvi: read_params_from_panel:' )
            eprint( '      red  band cannot be < 0' )
            eprint( '      ...returning' )
            return False

        nir = int( self.t_nb.GetValue().strip() )
        if nir < 0:
            eprint( 'ndvi: read_params_from_panel:' )
            eprint( '      nir band cannot be < 0' )
            eprint( '     ...returning' )
            return False
        
        self.p.red = red
        self.p.nir = nir

        return True
        
    def write_params_to_panel( self ):   # write parameters to panel
        
        red = str( self.p.red )
        self.t_rb.SetValue( red )
        
        nir = str( self.p.nir )
        self.t_nb.SetValue( nir )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        # source offset
        prompt_r = wx.StaticText( self.p_client, -1, 'red band:' )
        self.t_rb = wx.TextCtrl( self.p_client, -1, '' )
        #self.t_rb.Bind( wx.EVT_KEY_DOWN, self.on_file_key) 
        self.t_rb.SetToolTip( 'insert band number for red (580-680nM)' )
        
        prompt_n = wx.StaticText( self.p_client, -1, 'nir band:' )
        self.t_nb = wx.TextCtrl( self.p_client, -1, '' )
        #self.t_nb.Bind( wx.EVT_KEY_DOWN, self.on_file_key ) 
        self.t_nb.SetToolTip( 'insert band number for nir (725-1100nM)' )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL)
        h_sizer.Add( prompt_r, 0, wx.ALL, 6 )
        h_sizer.Add( self.t_rb, 0, wx.ALL, 1 )

        v_sizer.Add( h_sizer, 0 ,wx.ALL, 1 ) 

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( prompt_n, 0, wx.ALL, 6 )
        h_sizer.Add( self.t_nb, 0, wx.ALL, 1 )

        v_sizer.Add( h_sizer, 0, wx.ALL, 1 ) 

        # TODO: remove after study
        self.t_avg = wx.TextCtrl( self.p_client, -1, '' )
        v_sizer.Add( self.t_avg , 0, wx.ALL, 1 ) 

        self.p_client.SetSizer( v_sizer )

        self.write_params_to_panel()

    '''
    # intercept keystroke; look for CR
    def on_file_key( self, event ):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:   
            self.on_apply( None )     # as if pressing 'apply'
        event.Skip()                  # pass along event
    '''
    
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
        
    except Exception as e:  # FIXME: does this work?
        eprint( str(e) )
 
    os.remove( temp_name )
