#! /usr/bin/env python3

'''
@file npy_src.py
@author Scott L. Williams
@package POLI
@brief Reads a numpy pickle file.
@section LICENSE
# 
#  npy_src.py Copyright (C) 2016-2025 Scott L. Williams.
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
source operator for a pickled numpy file
'''

npy_src_copyright = 'npy_src.py Copyright (c) 2016-2025 Scott L. Williams,released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint
from urllib import request

# determine if graphics can be enabled
try:
    import wx
    from filedrop import FileDrop
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available  
 
# if not then assume non-graphics implementation
except:
    from op import op
    operator = op
    eprint( 'npy_src: using non-graphics mode.' )

def get_name(): 
    return 'npy_src'

# return an instance of 'npy_src' class 
def instantiate():	
    return npy_src( get_name() )

class npy_src_parameters( pio ):
    
    def __init__( self ):

        # FIXME: mmap == True (map_mode='r') doesn't work in np.load below
        self.mmap = False              # is source memory mapped?
        self.filepath = ''             # input numpy file
        self.apply_on_file_drop = True

    def print_params( self ):
        
        eprint( '\nparameters for npy_src:' )
        eprint( '                  mmap =', self.mmap )
        eprint( '              filepath =', self.filepath )
        eprint( '    apply on file drop =', self.apply_on_file_drop )

# -----------------------------------------------------------------------------

class npy_src( operator ):             # numpy source operator

    def __init__( self, name ): 
        
        operator.__init__(self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = npy_src_parameters()
        
    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    def use_cache( self, cache_path, mmode ):
        
        try:
            self.sink = np.load( cache_path,
                                 mmap_mode=mmode, # mmap flag
                                 allow_pickle=True )
 
            eprint( 'npy_src: using cached datafile:', cache_path )
 
        except:
            
            # not there, get and put in cache
            base = os.path.basename( self.p.filepath ) 
            eprint( 'npy_src: data file:', base,
                    'not in cache...retrieving' )

            # put in cache to load and for later use if needed
            try:
                eprint( 'npy_src: getting URL file:', self.p.filepath ) 
                request.urlretrieve( self.p.filepath, cache_path )
                            
            except Exception as e:
                
                eprint( e )
                eprint( 'npy_src: check above messages to see' )
                eprint( '         what went wrong...returning' )
                return
                                       
            self.sink = np.load( cache_path,
                                 mmap_mode=mmode, # mmap flag
                                 allow_pickle=True )
                        
            eprint( 'npy_src: using fresh URL datafile:', self.p.filepath )
     
    def URLload( self, mmode ):
        
        # get environment variables $POLI_HOME, $POLI_USE_CACHE
        POLI_HOME = os.environ['POLI_HOME']
        base = os.path.basename( self.p.filepath )
        cache_dir = POLI_HOME + '/.cache/'
        cache_path = cache_dir + base

        if not os.path.isdir( cache_dir ):
            os.mkdir( cache_dir )  # make directory if not there
 
        POLI_USE_CACHE = os.environ['POLI_USE_CACHE']
        eprint( 'npy_src: POLI_USE_CACHE=', POLI_USE_CACHE )
 
        if POLI_USE_CACHE in [ 'YES','Yes','Y','yes','y']:
            self.use_cache( cache_path, mmode )
                         
        elif POLI_USE_CACHE in [ 'NO','No','N','no','n']:
                    
            # put in cache to load and for later use if needed
            eprint( 'npy_src: getting URL file:', self.p.filepath ) 
            request.urlretrieve( self.p.filepath, cache_path )
            self.sink = np.load( cache_path,
                                 mmap_mode=mmode, # mmap flag
                                 allow_pickle=True )
        else:
            eprint( 'npy_src: bad value for environment variable:' )
            eprint( '         POLI_USE_CACHE=', POLI_USE_CACHE )
            eprint( '         use one of yes, no, y, n' )
            eprint( '         returning....' )
            raise Error( 'bad environment variable' )
 
    def run( self ):                   # override superclass run

        self.p.print_params()          # report parameters used
        self.print_versions()
        #self.source_name = self.p.filepath
        
        if self.p.mmap:          
            mmode = 'r'                # FIXME:doesn't work
            eprint( 'npy_src: using memory map mode' )
            
        else:
            mmode = None
            eprint( 'npy_src: using ram memory mode' )

        try:
            if self.p.filepath[:4] == 'http':
                self.URLload( mmode )         # sets self.sink
               
            else:
                # local filepath
                eprint( 'npy_src: getting local file:', self.p.filepath ) 
                self.sink = np.load( self.p.filepath,
                                     mmap_mode=mmode,
                                     allow_pickle=True )
        except OSError as e:
            
            eprint( e )
            eprint( 'npy_src: cannot open file: ' + self.p.filepath )
            self.sink = None
            return

        # accept only 2d or 3d  arrays
        if self.sink.ndim < 2 or self.sink.ndim > 3 :
            
            eprint( 'npy_src: bad number of dimensions, must be 2 or 3' )
            eprint( '            received dim= ' + data.ndim  )
            eprint( '            for file: ' + self.p.filepath )
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
        
        if isinstance( obj, str ):             # we've been invoked by
            obj.strip()                        # image_tree or file drop
            self.t_filepath.SetValue( obj )
            
        if self.p.apply_on_file_drop:
            self.on_apply( None )

    # override since we are a source and need to handle
    # thread slightly different
    def apply_work( self ):
        
        self.run()          # run the operator

        # check if valid run output
        if not isinstance( self.sink, np.ndarray ):
            eprint( 'npy_src: run output buffer not valid...returning' )
            return
        
        self.areal_index = None # reset areal to center image

        # buffer tags are lost; just enumurate
        nbands = self.sink.shape[2]
        self.band_tags = [ str(i) for i in range( nbands ) ]
        
    def read_params_from_panel( self ):       # scan panel parameters
        
        self.p.filepath = self.t_filepath.GetValue().strip()
        self.p.apply_on_file_drop = self.c_apply_on_file_drop.GetValue()

        return True

    def write_params_to_panel( self ):        # write parameters to panel
        
        self.t_filepath.SetValue( self.p.filepath )
        self.c_apply_on_file_drop.SetValue( self.p.apply_on_file_drop )

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
        
        eprint( '\nusage: npy_src.py' )
        eprint( '       -h, --help' )
        eprint( '       -f filepath, --file=filepath' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is filepath, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hf:p:', ['help','file=','params='])
        except getopt.GetoptError as e:
            eprint( 'npy_src: ' + str(e) )
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                usage()                     
                sys.exit( 0 )
                
            elif opt in ( '-f', '--file' ):
                self.p.filepath = arg
                
            elif opt in ( '-p', '--params' ):
                params = arg

        if params == None and self.p.filepath == '':
            eprint( 'npy_src: set_params: no input filename given' )
            sys.exit( 2 )

        if params != None:
            ok = self.read_params_from_file( str(params) )
            if not ok:
                eprint( 'npy_src: set_params: bad params file read' )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    
    oper = instantiate()                  # source point for pipe
    oper.set_params( sys.argv[1:] )
    oper.run()

    # send downstream
    oper.sink.dump( sys.stdout.buffer )
