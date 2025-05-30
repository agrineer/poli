'''
@file pio.py
@author Scott L. Williams.
@package POLI
@brief POLI parameter I/O
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
Super (base) class for POLI parameter I/O. This is an abstract class, don't call directly. 
'''
op_copyright = 'op.py Copyright (c) 2010-2025 Scott L. Williams, released under GNU GPL V3.0'

# super class for POLI parameters to handle file input and output
class pio():

    # initialize
    def __init__( self ):
        pass
    
     # get variables and values as a dictionary
    def get_state( self ):
        
        state = self.__dict__.copy()
        return state

    # read dictionary and set variabhle
    def set_state( self, state ):
        
        for key, value in state.items():
            setattr( self, key, value )


        
        
 
