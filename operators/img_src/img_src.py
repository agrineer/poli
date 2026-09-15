#! /usr/bin/env python

'''
@file img_src.py
@author Scott L. Williams.
@package POLI
@brief image source operator, can read jpg, jpeg, png, ie. generic PIL formats.
@LICENSE
#
#  img_src.py Copyright (C) 2010-2026 Scott L. Williams.
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
An image source operator for poli. Reads generic PIL image file types.
'''

img_src_copyright = 'img_src.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
from PIL import Image
from ezprint import eprint
from urllib import request

# determine if graphics can be enabled
try:
    import wx
    from filedrop import FileDrop
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command line or
                                       # batch mode when wx is available        
# if not, then assume batch or command line implementaion
except:
    from op import op
    operator = op
    #eprint( 'img_src: using non-graphics mode.' )

def get_name():
    return 'img_src'

# return an instance of 'img_src' class 
def instantiate():	
    return img_src()

class img_src_parameters( pio ):
    
    def __init__( self ):
        
        self.filepath = ''
        self.use_file_cache = False
        self.apply_on_file_drop = True
 
    def print_params( self ):
        
        eprint( '\nparameters for img_src:' )
        eprint( '               filepath =', self.filepath )
        eprint( '         use file cache =', self.use_file_cache )
        eprint( '     apply on file drop =', self.apply_on_file_drop )

# ----------------------------------------------------------------------------

class img_src( operator ):
    
    def __init__( self ): # initialize operator but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = img_src_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '     numpy =', np.version.version )

    def use_cache( self, cache_path ):
        
        try:
            image = Image.open( cache_path )
            eprint( 'img_src: using cached datafile:', cache_path )
 
        except:
            
            # not there, get and put in cache
            base = os.path.basename( self.p.filepath )
            eprint( 'img_src: data file:', base,
                    'not in cache...retrieving' )

            # put in cache to load and for later use if needed
            try:
                eprint( 'img_src: getting URL file:', self.p.filepath ) 
                request.urlretrieve( self.p.filepath, cache_path )
                            
            except Exception as e:
                eprint( e )
                eprint( 'img_src: check above messages to see' )
                eprint( '         what went wrong' )
                raise Error( 'img_src: unable to url retrieve' )
                                      
            image = Image.open( cache_path )
            eprint( 'img_src: using fresh URL datafile:', self.p.filepath )
 
        self.sink = np.array( image )

    def URLload( self ):
        
        # get environment variable POLI_HOME
        POLI_HOME = os.environ['POLI_HOME']
        base = os.path.basename( self.p.filepath )
        cache_dir = POLI_HOME + '/.cache/'
        cache_path = cache_dir + base

        if not os.path.isdir( cache_dir ):
            os.mkdir( cache_dir )  # make directory if not there
 
        if self.p.use_file_cache:
            self.use_cache( cache_path )
   
        else:
                    
            # put in cache for later use if needed
            eprint( 'img_src: getting URL file:', self.p.filepath )
            try:
                request.urlretrieve( self.p.filepath, cache_path )
                image = Image.open( cache_path )
                self.sink = np.array( image )
                
            except Exception as e:
                eprint( str(e) )
                raise Error( 'img_src: URLload: bad url retrieval' )
        
    def run( self ):            # override superclass run

        self.p.print_params()   # report parameters used when running
        self.print_versions()

        if self.p.filepath == '':
            eprint( 'img_src: run: filepath not given...returning' )
            return
        
        try:
            if self.p.filepath[:4] == 'http':
                self.URLload()  # sets self.sink
                 
            else:
                
                eprint( 'img_src: getting local file:', self.p.filepath )  
                image = Image.open( self.p.filepath )
                self.sink = np.array( image )

        except OSError as e:
            eprint( e )
            eprint( 'img_src: cannot open file: ' + self.p.filepath )
            self.sink = None
            return
        
        # accept only 2d or 3d arrays
        if self.sink.ndim < 2 or self.sink.ndim > 3 :
            eprint( 'img_src: bad number of dimensions, must be 2 or 3' )
            eprint( '         received dim= ' + self.sink.ndim  )
            eprint( '         for file:', filepath )
            self.sink = None
            return

        # make 2d buffer into 1 band 3d buffer
        if self.sink.ndim == 2 :
            height,width = self.sink.shape
            self.sink.shape = height,width,1

    ####################################################################
    # gui section
    ####################################################################

    def set_filepath( self, obj ):
        
        if isinstance(obj, str):             # we've been invoked by
            obj.strip()                      # image_tree or file drop
            self.t_filepath.SetValue( obj )
            
        if self.p.apply_on_file_drop:
            self.on_apply( None )

    # overide since we are a source and need to handle
    def apply_work( self ):
        
        self.run()            # run the operator

        # check if valid run output
        if not isinstance( self.sink, np.ndarray ):
            eprint( 'img_src: run output buffer not valid...returning' )
            return
        
        self.areal_index = None # reset areal to center image
       
        # generic buffer tags 
        nbands = self.sink.shape[2]
        if nbands == 1:
            self.band_tags = ['grey']
        else:
            self.band_tags = ['red','green','blue']

    # scan panel parameters
    def read_params_from_panel( self ):
        
        self.p.apply_on_file_drop = self.c_apply_on_file_drop.GetValue()
        self.p.use_file_cache = self.c_use_file_cache.GetValue()
        self.p.filepath = self.t_filepath.GetValue().strip() 
 
        return True
    
    # write parameters to panel
    def write_params_to_panel( self ):
       
        self.c_apply_on_file_drop.SetValue( self.p.apply_on_file_drop )
        self.c_use_file_cache.SetValue( self.p.use_file_cache )
        self.t_filepath.SetValue( self.p.filepath )
 
    # initialize graphics
    def init_panel( self, benchtop ):
        
        operator.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.AddSpacer( 10 )  # space from top

        # make checkbox panel
        panel = self.checkboxes_panel()
        v_sizer.Add( panel )
        v_sizer.AddSpacer( 25 )  # add space

        # make filepath text control panel
        panel = self.filepath_panel()
        v_sizer.Add( panel, 1, wx.EXPAND )

        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    # make filepath panel
    def filepath_panel( self ):

        # make panel for filepath
        p_filepath = wx.Panel( self.p_client, -1 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.AddSpacer( 7 ) # spacer from left

        # file input text control
        prompt = wx.StaticText( p_filepath, -1, 'enter image file: ' )
        h_sizer.Add( prompt )
        
        self.t_filepath = wx.TextCtrl( p_filepath, -1, '' )
        self.t_filepath.SetToolTip( 'enter filepath' )
        dt = FileDrop( self.t_filepath, self )
        self.t_filepath.SetDropTarget( dt )

        h_sizer.Add( self.t_filepath, 1, wx.EXPAND )
        h_sizer.AddSpacer( 4 )
        
        b_browse = wx.Button( p_filepath, -1, 'browse' )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )

        h_sizer.Add( b_browse )
        
        p_filepath.SetSizer( h_sizer )
        return p_filepath

    # make checkboxes panel
    def checkboxes_panel( self ):
        
        p_checkboxes = wx.Panel( self.p_client, -1 )

        v_sizer = wx.BoxSizer( wx.VERTICAL )

        # use file cache
        self.c_use_file_cache = wx.CheckBox( p_checkboxes, -1, 'use file cache')
        self.c_use_file_cache.SetToolTip( 'enables/disables use of a cached' +
                                          ' file')
        v_sizer.Add( self.c_use_file_cache )
        v_sizer.AddSpacer( 10 )  # add space between checkboxes
        
        # file drop
        self.c_apply_on_file_drop = wx.CheckBox( p_checkboxes, -1,
                                                 'apply on file drop' )
        self.c_apply_on_file_drop.SetToolTip( 'immediate execution when file' +
                                              ' is dropped or by double' +
                                              ' clicking the data file in' +
                                              ' data suites' )
        
        self.c_apply_on_file_drop.Bind( wx.EVT_LEFT_UP, self.on_file_drop )
        v_sizer.Add( self.c_apply_on_file_drop )
       
        p_checkboxes.SetSizer( v_sizer )
        return p_checkboxes 

    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, "Choose an image to read", 
                             os.getcwd(), "", "*", wx.FD_OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath().strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

    def on_file_drop( self, event ):
        
        # could use not function but this is easier to read
        if self.c_apply_on_file_drop.GetValue():
            self.p.apply_on_file_drop = False
        else:
            self.p.apply_on_file_drop = True
  
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: img_src.py' )
        eprint( '       -h, --help' )
        eprint( '       -c, --cache  use file cache flag' )
        eprint( '       -f filepath, --file=filepath' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'output is stdout' )

    # params file not really needed for just one argument
    # but include anyway
    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hcf:p:', ['help','file=',
                                                   'cache', 'params='])
        except getopt.GetoptError as e:
            eprint( 'img_src: ' + str(e) )
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                usage()                     
                sys.exit( 0 )

            elif opt in ('-c', '--cache' ):
                self.p.use_file_cache = True
        
            elif opt in ( '-f', '--file' ):
                self.p.filepath = arg
                
            elif opt in ( '-p', '--params' ):
                params = arg
               
        if params == None and self.p.filepath == '':
            
            eprint( 'img_src: set_params: no input filename given' )
            self.usage()
            sys.exit( 2 )

        if params != None:
            
            ok = self.read_params_from_file( str(params) )
            if not ok:
                eprint( 'img_src: set_params: bad params file read...exiting' )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    
    try:
        oper = instantiate()           # source point for pipe
        oper.set_params( sys.argv[1:] )
        oper.run()            
        oper.sink.dump( sys.stdout.buffer )   # send downstream
        
    except Exception as e:
        eprint( str(e) )
