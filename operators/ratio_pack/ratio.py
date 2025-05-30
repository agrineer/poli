#! /usr/bin/env /usr/bin/python

#  ratio.py
# 
#  Copyright (C) 2012 Scott L. Williams.
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

poli_copyright = 'ratio.py Copyright (c) 2012 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

# ratio operator for poli using red and nir bands
# shows red/nir ratios

import wx
import sys
import getopt
import numpy as np

from op_panel import op_panel

# return an instance of 'ratio' class 
# without having to know its name
def instantiate():	
    return ratio( get_name() )

def get_name(): 
    return 'ratio'

class ratio_parameters():           # hold arguments values here
    def __init__( self ):
        pass

class ratio( op_panel ):
    def __init__( self, name ):      # initialize op_panel but no graphics
        self.op_id = 'ratio version 0.0'
        self.params = ratio_parameters()
        op_panel.__init__( self, name )
        
    def run( self ):                 # override superclass run      

        # make buffers float
        red = self.source[:,:,0].astype( np.float )
        nir = self.source[:,:,1].astype( np.float )

        red_avg = np.average( red )
        nir_avg = np.average( nir )
        print red_avg, nir_avg

        self.sink = red/nir

        # make 3-d
        heigth, width = self.sink.shape
        self.sink.shape = (heigth,width,1)
        
    ############################################################
    # command line options
    ############################################################

    # TODO: update
    def usage( self ):
        print >> sys.stderr, 'usage: ratio.py'
        print >> sys.stderr, '       -h, --help'
        print >> sys.stderr, '       -r value, --ratio=value'
        print >> sys.stderr, '       -p paramfile, --params=paramfile'
        print >> sys.stderr, '       param file overrides line arguments'
        print >> sys.stderr, '       input is stdin, output is stdout'

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hp:r:', 
                                        ['help','ratio='])
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0) 
            elif opt in ( '-r', '--ratio' ):                
                self.params.red = int(arg)
            elif opt in ('-p', '--params'):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                sys.exit(2)
                
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        pass
        
    def write_params_to_panel( self ):   # write parameters to panel
        pass

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

    # intercept keystroke; look for CR
    def on_file_key( self, event ):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:   
            self.on_apply( None )     # as if pressing 'apply'
        event.Skip()                  # pass along event

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':          
    oper = instantiate()   
    oper.set_params( sys.argv[1:] )

    oper.source = np.load( sys.stdin )    # input is upstream
    oper.run()                  
    oper.sink.dump( sys.stdout )          # send downstream    
