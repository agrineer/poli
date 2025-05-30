#! /usr/bin/env python3

'''
@file sobel.py
@author Scott L. Williams.
@package POLI
@brief skimage sobel edge detection
@LICENSE
# 
#  sobel.py Copyright (C) 2010-2025 Scott L. Williams.
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

@sections DESCRIPTION
Find the vertical and/or vertical edges of an image using the Sobel transform.

'''

sobel_copyright = 'sobel.py Copyright (c) 2010-2025 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import scipy
import getopt
import numpy as np
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
    eprint( 'sobel: using non-graphics mode.' )

def get_name(): 
    return 'sobel'

# return an instance of 'sobel' class 
def instantiate():	
    return sobel( get_name() )

class sobel_parameters( pio ):             # hold arguments values here
    
    def __init__( self ):
        self.sdir = 2                      # options: 0=x, 1=y, 2=xy

    def print_params( self ) :
        
        eprint( '\nparameters for sobel:' )
        
        if self.sdir == 2:
            eprint( '    dir = 2 (xy direction)' )

        if self.sdir == 1:
            eprint( '    dir = 1 (y direction)' )

        if self.sdir == 0:
            eprint( '    dir = 0 (x direction)' )
 
class sobel( operator ):
    
    def __init__( self, name ):       # initialize op_panel but no graphics
        
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = sobel_parameters()
      
    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
        eprint( '   scipy =', scipy.version.version )
        
    def run( self ):                  # override superclass run
        
        self.p.print_params()         # report parameters used when running
        self.print_versions()

        height,width,nbands = self.source.shape
        self.sink = np.empty( (height,width,nbands), dtype=np.float32 )

        # use floats
        if self.source.dtype != np.float32:
            self.source = self.source.astype( np.float32 )
        
        if self.p.sdir == 2:

            for i in range(0,nbands):
                dx = scipy.ndimage.sobel( self.source[:,:,i], 0 )
                dy = scipy.ndimage.sobel( self.source[:,:,i], 1 )
                mag = np.sqrt( dx**2 + dy**2)
                mag *= 255.0 / np.max( mag )  # normalization
                self.sink[:,:,i] = mag[:,:]
                
        else:
            
            for i in range(0,nbands):
                edge = scipy.ndimage.sobel( self.source[:,:,i], self.p.sdir )
                mag = np.sqrt( edge**2 )
                mag *= 255.0 / np.max( mag )  # normalization
                self.sink[:,:,i] = mag[:,:]
 
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        
        if self.r_vert.GetValue():
            self.p.sdir = 0
            
        if self.r_horiz.GetValue():
            self.p.sdir = 1
            
        if self.r_both.GetValue():
            self.p.sdir = 2

        return True

    def write_params_to_panel( self ):   # write parameters to panel
        
        if  self.p.sdir == 0:
            self.r_vert.SetValue( True )
            
        if  self.p.sdir == 1:
            self.r_horiz.SetValue( True )
            
        if  self.p.sdir == 2:
            self.r_both.SetValue( True )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        # make radio panel
        p_radio = wx.Panel( self.p_client, -1, (10,2), (100,90) )

        sizer = wx.GridBagSizer( 2, 1 )

        #  mark the beginning of the group with wx.RB_GROUP
        self.r_horiz = wx.RadioButton( p_radio, -1, 'horizontal', 
                                      style = wx.RB_GROUP )
        self.r_vert = wx.RadioButton( p_radio, -1, 'vertical' )
        self.r_both = wx.RadioButton( p_radio, -1, 'both' )

        sizer.Add ( self.r_horiz, (0,0) )
        sizer.Add ( self.r_vert, (1,0) )
        sizer.Add ( self.r_both, (2,0) )

        p_radio.SetSizer( sizer )
        self.write_params_to_panel()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: sobel.py' )
        eprint( '       -h, --help' )
        eprint( '       -d <0,1,2>, --dir=<0,1,2>  where x=0,y=1,xy=2')
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 'hd:p:',
                                        ['help','dir=','params='])
        except getopt.GetoptError as e:
            eprint( 'sobel: ' + str(e) )           
            self.usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            elif opt in ( '-d', '--dir' ):
                
                if arg in ['0','1','2']:
                    self.p.sdir = int( arg )
                else:
                    eprint( 'sobel: bad direction:', arg, ' ...exiting' )
                    sys.exit( 2 )                 

        if params != None:
            
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'sobel: set_params: bad params file read' )
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
