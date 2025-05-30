'''
@file filedrop.py
@author Scott L. Williams.
@package POLI
@brief adapted filedrop class for POLI
@LICENSE
#
#  filedrop.py Copyright (C) 2010-2025 Scott L. Williams.
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
POLI operators, which require a file input, can use this class to facilitate
filepath entry. Source operators, operators with look-up table files, or other
operators with a need for a file can use this class. Instantiation is done
in the POLI wxPython panel implementation
'''

import wx
from ezprint import eprint

class FileDrop( wx.FileDropTarget ): 
        
    def __init__( self, window, operator ):
            
        wx.FileDropTarget.__init__(self)
        self.window = window
        self.operator = operator

    # url prefixes get removed as do trailing non-printables
    # just by running throughg this method; if not intercepted
    # url prefixes and non-printable characters appear
    def OnDropFiles( self, x, y, filenames ):
            
        try:
            self.window.SetValue( filenames[0] ) # use just the first name
            if self.operator.p.apply_on_file_drop:
                self.operator.on_apply( None )
            return True
            
        except Exception as e:
            eprint( e )
            eprint( 'img_src: something went wrong with file drop...' )
            return False
