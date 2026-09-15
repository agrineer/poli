#! /usr/bin/env python

'''
@file flip.py
@author Scott L. Williams.
@package POLI
@brief flip an image
@LICENSE
#
#  flip.py Copyright (C) 2010-2026 Scott L. Williams.
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
flip the input buffers
'''

flip_copyright = 'flip.py Copyright (c) 2010-2026 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

#  flip operator for poli 
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
    eprint( 'flip: using non-graphics mode.' )

def get_name(): 
    return 'flip'

# return an instance of 'flip' class 
def instantiate():	
    return flip()

class flip_parameters( pio ):       # hold arguments values here

    def __init__( self ):
        self.fdir = 'x'        # options are x, y, xy

    def print_params( self ):       
        eprint( '\nparameters for flip:' )
        eprint( '                 dir =', self.fdir )
    
# ----------------------------------------------------------------------------

class flip( operator ):
    
    def __init__( self ):      # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = flip_parameters()
        
    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
    
    def run( self ):                 # override superclass run

        self.p.print_params()        # report parameters as op is run
        self.print_versions()
 
        if self.p.fdir == 'x' or self.p.fdir == 'X':
            self.sink = np.fliplr( self.source )
            
        elif self.p.fdir == 'y' or self.p.fdir == 'Y':
            self.sink = np.flipud( self.source )
            
        elif self.p.fdir == 'xy' or self.p.fdir == 'XY':
            self.sink = np.swapaxes( self.source, 1, 0 )
            
        else:
            eprint( 'flip: unknown option' )
            return

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        
        if self.r_x.GetValue():
            self.p.fdir = 'x'

        elif self.r_xy.GetValue():
            self.p.fdir = 'xy'
            
        elif self.r_y.GetValue():
            self.p.fdir = 'y'
           
        return True
    
    def write_params_to_panel( self ):   # write parameters to panel
        
        if self.p.fdir == 'x':
            self.r_x.SetValue( True )
            
        elif self.p.fdir == 'xy':
            self.r_xy.SetValue( True )

        elif self.p.fdir == 'y':
            self.r_y.SetValue( True )

        else:
            eprint( 'flip: write_params_from_panel: unknown dir value =',
                    self.p.fdir, ' ...returning' )
            
    # initialize graphics
    def init_panel( self, benchtop ):
        
        operator.init_panel( self, benchtop ) # start with basics

        # lay out sizers for future panels
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        panel = self.fdir_panel()

        h_sizer.Add( panel )
        v_sizer.Add( h_sizer )

        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    def fdir_panel( self ):
        
        p_fdir = wx.Panel( self.p_client, -1, style=wx.SUNKEN_BORDER )
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
 
        self.r_x = wx.RadioButton( p_fdir, -1, 'x', style = wx.RB_GROUP )
        v_sizer.Add( self.r_x )
        v_sizer.Add( (1,1) )

        self.r_y = wx.RadioButton( p_fdir, -1, 'y' )
        v_sizer.Add( self.r_y )
        v_sizer.Add( (1,1) )

        self.r_xy = wx.RadioButton( p_fdir, -1, 'xy' )
        v_sizer.Add( self.r_xy )
        v_sizer.Add( (1,1) )

        p_fdir.SetSizer( v_sizer )

        return p_fdir
        
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: flip.py' )
        eprint( '       -h, --help' )
        eprint( '       -d <x,y,xy>, --dir=<x,y,xy>' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )
        sys.exit( 2 )  
 
    def set_params( self, argv ):
        
        params = None
 
        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hp:d:', ['help','param=','dir='])
        except getopt.GetoptError as e:
            eprint( 'flip: ' + str(e) )
            self.usage()                          
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):
                eprint( 'flip: unknown argument:' )
                self.usage()                     
                sys.exit( 0 )
                
            if opt in ( '-d', '--dir' ):
                
                if arg not in ['x', 'X', 'y', 'Y', 'xy', 'XY' ]:
                    self.usage()
                    sys.exit( 2 )
                    
                self.p.fdir = arg
                
            elif opt in ( '-p', '--params' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'flip: cannot find file:', arg, ' ...exiting' )
                    sys.exit( 2 )
                else:
                    params = arg

        if params != None:
           
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'flip: set_params: bad params file read' )
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
