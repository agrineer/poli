'''
@file op.py
@author Scott L. Williams.
@package POLI
@section LICENSE 

#  Copyright (C) 2010-2025 Scott L. Williams.

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

@section DESCRIPTION
Super (base) class for POLI operators. This is an  abstract class, don't call directly. 
'''
op_copyright = 'op.py Copyright (c) 2010-2025 Scott L. Williams, released under GNU GPL V3.0'

import os
import ast
import sys
import time
from ezprint import eprint

class op():

    # initialize
    def __init__( self, name ):
        self.name = name        # operator name
        self.__version__ = None

        self.source = None      # 3d areal source image to process
        self.sink = None        # 3d areal output image

        self.p = None           # parameter object

    # override this method in subclass
    def run( self ):
        eprint( 'op: run: this method should not be called directly' )

    # get this operator's parameters from file 
    def read_params_from_file( self, filename ):

        try:
            sfile = open( filename, 'r' )
            pdict = sfile.read()

            # use string dictionay to set parameters 
            state = ast.literal_eval( pdict ) 
            self.p.set_state( state )
            
        except Exception as e:
            eprint( e )
            return False
            
        return True

    # pickle and store parameter values
    def write_params_to_file( self, filename ):

        try:
            # get varibles and values as a dictionary
            state = self.p.get_state()

            # write dictionary to file as a string
            sfile = open( filename, 'w' )           
            sfile.write( str(state) )
            
        except Exception as e:
            eprint( e )
            return False
            
        return True

        
        
 
