#! /usr/bin/env python

'''
@file append.py
@author Scott L. Williams.
@package POLI
@brief append the source buffer to current buffer.
@LICENSE
# 
#  append.py Copyright (C) 2020-2026 Scott L. Williams.
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
append_copyright = 'append.py Copyright (c) 2020-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from ezprint import eprint

# determine if graphics can be enabled
try:
    import wx
    from op_panel import op_panel
    operator = op_panel                 # uses op_panel in command
                                        # line/batch mode when wx is available
# if not then assume batch implementaion
except:
    from op import op
    operator = op
    #eprint( 'append: using non-graphics mode.' )

def get_name():                
    return 'append'

# return an instance of 'append' class 
def instantiate():
    return append()

class append_parameters():              # hold arguments values here
    
    def __init__( self ):
        pass
    
    def print_params( self ):
        eprint( '\nappend does not have parameters' )
        
# ---------------------------------------------------------------------------

class append( operator ):
    
    def __init__( self ):         # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = append_parameters()    # no parameters yet

        self.empty = True
        self.height = None
        self.width = None
        self.nbands = None

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
         
    def run( self ):                    # override superclass run

        self.p.print_params()           # report parameters used when running
        self.print_versions()
 
        eprint( 'append: there are no parameters to report' )
        self.print_versions()

        if self.empty:
            
            # use source buffer as initial buffer
            self.sink = self.source

            # save shape for later checks
            self.height,self.width,self.nbands = self.source.shape

            self.empty = False
            return
        
        # get new image shape to check old width and nbands
        height,width,nbands = self.source.shape
        if self.width != width:
            eprint( 'append: run: widths do not match: ', self.width, width )
            return
        
        if self.nbands != nbands:
            eprint( 'append: run: nbands do not match: ', self.nbands, nbands )
            return
        
        self.sink = np.append( self.sink, self.source, axis=0 )
        
    ####################################################################
    # gui section
    ####################################################################

    # set up processing; called from app over-rides op_panel apply_work
    def apply_work( self ):           

        # get input image from a neighbor operator
        self.source = self.get_source( 1 )
        
        # is neighbor sink image set?
        #if type( self.source ) is not np.ndarray:
        if not isinstance( self.source, np.ndarray ):
            eprint( 'append: apply_work: ' + \
                   'neighbor sink (output) image not set' )
            return

        if self.empty:
            self.set_areal_tags( 1 )        # inherit nav and band tags
            self.run()                      # run the operator

        else:
            self.run()

            # append nav data if any
            # FIXME: if current image has nav data but but appending does not
            #        then fill nav data with Nones or Nans
            try: 
                #if type( self.nav_data ) is np.ndarray:
                if isinstance( self.nav_data, np.ndarray ):
                    src_op = self.get_source_op( 1 )
                    
                    #if type( src_op.nav_data ) is np.ndarray:
                    if isinstance( src_op,nav_data, np.ndarray ):
                        self.nav_data = np.append( self.nav_data,
                                                   src_op.nav_data,
                                                   axis=0 )
            except:
                pass

            self.areal_index = None # centers and scales new image

    def read_params_from_panel( self ):
        return True

    def write_params_to_panel( self ):
        pass

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: append.py' )
        eprint( '       -h, --help' )
        eprint( '       input is stdin, output is stdout' )

    def set_params( self, argv ):

        try:                                
            opts, args = getopt.getopt( argv, 'h', ['help'])
            
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
                
####################################################################
# command line user entry point 
####################################################################

# append does not play well with streaming as it needs 2 inputs
# but can used in batch
