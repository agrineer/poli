#! /usr/bin/env python3

'''
@file poli.py
@author Scott L. Williams
@ package POLI
@ brief initiate the POLI grogram
@ section LICENSE

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
#

@section DESCRIPTION
Launch point for POLI (Python On Line Imaging). 
'''

poli_copyright = 'poli.py Copyright (c) 2010-2025 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

import os
import wx
import sys
import getopt
from benchtop import benchtop

class main_frame( wx.Frame ):    # frame container class for poli window

    def __init__( self, config_file ): 

        if config_file == None:
            print( 'main_frame: config_file cannot be None...exiting',
                   file=sys.stderr )
            sys.exit( 1 )
                   
        if not os.path.isfile( config_file ) :
            print( 'poli: config file: ' + config_file + ' does not exist',
                   file=sys.stderr )
            print( 'exiting...', file=sys.stderr )
            sys.exit( 1 )

        wx.Frame.__init__( self, None, -1, "" )

        self.SetTitle( 'POLI - Python On Line Imaging' )

        rect = wx.ClientDisplayRect()    # get system screen size
        size_x = int(rect[2]/(3/2))         # 

        self.SetSize( (size_x,rect[3]) ) 
  
        # TODO: get parrot icon
        # self.SetIcon( wx.Icon('poli.ico', wx.BITMAP_TYPE_ICO))
        '''
        # build the menu bar
        file_menu = wx.Menu()   
        item = file_menu.Append( wx.ID_EXIT, text="&Quit" )
        self.Bind( wx.EVT_MENU, self.on_quit, item )

        # TODO: bind to quit X title bar
        menu_bar = wx.MenuBar()     
        menu_bar.Append( file_menu, "&File" )
        self.SetMenuBar( menu_bar )

        # responds to exit symbol x on frame title bar
        self.Bind( wx.EVT_CLOSE, self.on_close )
        '''
        #         self.build_menu()
        
        # setup frame scrolling
        self.scroller = wx.ScrolledWindow( self )
        self.scroller.SetScrollRate(1,1)
        self.scroller.EnableScrolling(True,True)
 
        # bring it all up
        self.benchtop = benchtop( self.scroller, config_file )
        self.benchtop.SetMinSize( (528, 546) )   # refer to benchtop layout
                                                 # for current size
        sizer = wx.BoxSizer()                    # put the panel in a sizer 
        sizer.Add( self.benchtop, 1, wx.EXPAND ) # for the frame to manage
        self.scroller.SetSizer( sizer )
              
        self.Bind( wx.EVT_SIZE, self.on_resize ) # bind resize event

    def on_resize( self, event ):
        size = self.GetClientSize()   # report frame size to benchtop 
        self.benchtop.layout( size )  # to resize itself
        self.scroller.SetSize( size )

        event.Skip()

    def on_close( self, event ):# really exit 

        # clean up before exiting
        #self.benchtop.finalize()
        event.Skip()

    def on_quit( self, event=None ):
        self.Close()         # exit application

# --------------------------------------------------------
# command line utilities

def usage():
    print( 'usage for poli.py:', file=sys.stderr )
    print( '       -h, OR --help', file=sys.stderr ) 
    print( '       -c configfile OR --configfile=configfile', file=sys.stderr )
 #   print( '       -v OR --verbose', file=sys.stderr )
    print( 'if no configuration file is given then a default one will be used',
           file=sys.stderr )

def get_params( argv ):

    # set default configuration file
    poli_home= os.getenv( 'POLI_HOME' )
    config_file = poli_home + '/projects/default.ini'

    # FIXME: cannot catch unknown arguments
    try:                                
        opts, args = getopt.getopt( argv, 'hc:',
                                    ['help','configfile='] ) 
    except getopt.GetoptError:
        print( sname, 'argument exception: unknown flag(s)',
               argv, file=sys.stderr )
        usage()                          
        sys.exit( 2 )  

    # set options now and error check later
    for opt, arg in opts:
        if opt in [ '-h', '--help' ]:      
            usage()                     
            sys.exit( 0 )

        elif opt in [ '-c', '--configfile' ]:
            config_file = arg.strip()

   # checking parameter values; includes default values, if used
    if not os.path.isfile( config_file ):
        print( sname, 'ERROR: datafile:', config_file,
                ' does not exist ...exiting', file=sys.stderr, flush=True )
        sys.exit( 1 )

    print( 'poli: using config file:', config_file,
           file=sys.stderr, flush=True )

    return config_file

if __name__ == '__main__':   # user entry point

    # report environment information
    sname = sys.argv[0]
    print( 'running Python script:', sname, file=sys.stderr, flush=True )
    print( 'using Python version', sys.version, file=sys.stderr, flush=True )

    # check if environment variable $POLI_HOME is set
    if 'POLI_HOME' not in os.environ:
        print( 'poli: environment variable $POLI_HOME is NOT set. exiting.',
               file=sys.stderr )
        sys.exit( 1 )

    # get configuration file from command line
    # all parameters given in config file, and so no extra parsing
    # if no config parameter file is given then default project is used
    config_file = get_params( sys.argv[1:] )
    if not os.path.isfile( config_file ):
        print( 'poli: config file', config_file, 'does not exist ... exiting',
               file=sys.stderr, flush=True )
        sys.exit( 1 )
        
    app = wx.App()

    frame = main_frame( config_file )
    frame.Show()

    app.MainLoop()
