#! /usr/bin/env python3

'''
@file mod02_src.py
@author Scott L. Williams
@package POLI
@brief MODIS data source for modis data type 2
@License
# 
#  Copyright (C) 2010-2025 Scott L. Williams.
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
A MODIS data source point for type 2 level 1b data.
Source is calibrated radiometrically and contains geo-referenced (centered)
pixels. 
'''

mod02_src_copyright = 'mod02_src.py Copyright (c) 2010-2025 Scott L. Williams released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint
from urllib import request

try:
    from mod02_src.mod02_hdf import mod02_hdf # using GUI
    
except Exception as e:
    #eprint( e )
    from mod02_hdf import mod02_hdf           # non-GUI..
                                              # loads twice due to module name
    eprint( 'mod02_src: using non-graphics mode' )

# determine if graphics can be enabled
try:
    import wx
    from filedrop import FileDrop
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
        
# if not, then assume batch or command line implementaion
except:
    from op import op
    operator = op
    eprint( 'mod02_src: using non-graphics mode.' )

def get_name(): 
    return 'mod02_src'

# return an instance of 'mod02_src' class 
def instantiate():	
    return mod02_src( get_name() )

class mod02_src_parameters( pio ):
    
    def __init__( self ):
        
        self.filepath = ''             # input modis file
        self.readnav = False           # read navigation data 
        self.readsolar = False         # read solar angles into buffers
        self.readsensor = False        # read sensor angles into buffers
        self.swconv = 1                # shortwave conv:0-radiance 1-reflectance
        self.bandstr = ''              # bands to read in

        self.apply_on_file_drop = True

    def print_params( self ):
        
        eprint( '\nparameters for mod02_src:' )
        eprint( '    filepath            =', self.filepath )
        eprint( '    read lat/lon        =', self.readnav )
        eprint( '    read solar angles   =', self.readsolar )
        eprint( '    read sonsor angles  =', self.readsolar )
        eprint( '    shortwave conv      =', self.swconv )
        eprint( '    band string         =', self.bandstr )

        '''
        eprint( '    calc lat lon        =', self.calc_latlon )
        eprint( '    top left latitude   =', self.tl_lat )
        eprint( '    top left longitude  =', self.tl_lon )
        eprint( '    bot right latitude  =', self.br_lat )
        eprint( '    bot right longitude =', self.br_lon )
        '''
        
        eprint( '    apply on file drop  =', self.apply_on_file_drop )
        
#-----------------------------------------------------------------------

class mod02_src( operator ):           # image source operator
    
    def __init__( self, name ):        # initialize op_panel but no graphics
        
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = mod02_src_parameters()

    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
        
    def use_cache( self, mod, cache_path ):
        
        try:
            mod.open_file( cache_path )     
            eprint( 'projmod_src: using cached datafile:', cache_path )
 
        except:
            
            # not there, get and put in cache
            base = os.path.basename( self.p.filepath )
            eprint( 'mod02_src: data file:', base,
                    'not in cache...retrieving' )

            # put in cache to load and for later use if needed
            try:
                eprint( 'mod02_src: getting URL file:', self.p.filepath ) 
                request.urlretrieve( self.p.filepath, cache_path )
                            
            except Exception as e:
                eprint( e )
                eprint( 'mod02_src: check above messages to see' )
                eprint( '             what went wrong...returning' )
                                       
            mod.open_file( cache_path )     
            eprint( 'mod02_src: using fresh URL datafile:', self.p.filepath )
        
    def URLload( self, mod ):
        
        # get environment variables $POLI_HOME, $POLI_USE_CACHE
        POLI_HOME = os.environ['POLI_HOME']
        base = os.path.basename( self.p.filepath )
        cache_dir = POLI_HOME + '/.cache/'
        cache_path = cache_dir + base

        if not os.path.isdir( cache_dir ):
            os.mkdir( cache_dir )  # make directory if not there
 
        POLI_USE_CACHE = os.environ['POLI_USE_CACHE']
        eprint( 'mod02_src: POLI_USE_CACHE=', POLI_USE_CACHE )
 
        if POLI_USE_CACHE in [ 'YES','Yes','Y','yes','y']:
            self.use_cache( mod, cache_path )
                         
        elif POLI_USE_CACHE in [ 'NO','No','N','no','n']:
                    
            # put in cache to load and for later use if needed
            eprint( 'mod02_src: getting URL file:', self.p.filepath ) 
            request.urlretrieve( self.p.filepath, cache_path )
            mod02.open_file( cache_path )     
 
        else:
            eprint( 'mod02_src:  bad value for environment variable:' )
            eprint( '              POLI_USE_CACHE=', POLI_USE_CACHE )
            eprint( '              use one of yes, no, y, n' )
            eprint( '              returning....' )
            raise Error( 'bad environment variable' )

    def str2tuple(self, s):
        
        items = s.split(',')           # convert tuple-like strings 
                                       # to real tuples.
                                       # eg '1,2,3,4' -> (1, 2, 3, 4)
        t = [x.strip() for x in items] # clean up spaces
        return tuple( t )

    def run( self ):                   # override superclass run

        self.p.print_params()          # report parameters used when running
        self.print_versions()

        if self.p.bandstr == '':
            eprint( 'mod02_src: run: band string is empty...returning' )
            return
 
        mod = mod02_hdf()

        try:
            if self.p.filepath[:4] == 'http':
                self.URLload( mod )  

            else:
                
                eprint( 'mod02_src: getting local file:', self.p.filepath )
                mod.open_file( self.p.filepath ) 
              
                if mod.hdf_sd == None:
                    eprint( 'mod02_src: cannot open file:' + self.p.filepath )
                    self.sink = None
                    return

        except OSError as e:
            eprint( e )
            eprint( 'mod02_src: cannot open file: ' + self.p.filepath )
            self.sink = None
            return

        mod.open_file( self.p.filepath ) 
        if mod.hdf_sd == None:
            self.sink = None
            return

        self.source_name = self.p.filepath

        mod.read_attributes()          # get modis type, sets sizes

        stuple = self.str2tuple( self.p.bandstr )
        nbuf = len( stuple )
        
        if self.p.readsolar:
            nbuf += 2
            
        if self.p.readsensor:
            nbuf += 2
            
        self.sink = np.empty( (mod.height,mod.width,nbuf),
                              dtype=np.float32 )
        self.sink.fill( np.nan )

        index = 0
        self.band_tags = []

        if self.p.swconv == 0:    # determine shortwave conversion
            swconv = 'radiance'
            
        elif self.p.swconv == 1:
            swconv = 'reflectance'

        for i in stuple:           
            band,tag = mod.readband( i, swconv )

            if type( band ) is np.ndarray:
                self.sink[:,:,index] = band
                self.band_tags.append( tag )
            else:
                self.band_tags.append( 'none' )
                
            index += 1

        if self.p.readnav:
            
            self.nav_tags = []
            self.nav_data = np.empty( (mod.height,mod.width,2),
                                      dtype=np.float32 )
            
            self.nav_data[:,:,0] = mod.readangles( 'Latitude' )
            if type( self.nav_data[:,:,0] ) is np.ndarray:
                self.nav_tags.append( 'lat' )
                     
            self.nav_data[:,:,1] = mod.readangles( 'Longitude' )
            if type( self.nav_data[:,:,1] ) is np.ndarray:
                self.nav_tags.append( 'lon' )

        if self.p.readsolar:
            
            self.sink[:,:,index] = mod.readangles( 'SolarZenith' )
            if type( self.sink[:,:,index] ) is np.ndarray:
              self.band_tags.append( 'sol. zenith' )
            else:
                self.band_tags.append( 'none' )
                     
            index += 1
            self.sink[:,:,index] = mod.readangles( 'SolarAzimuth' )
            if type( self.sink[:,:,index] ) is np.ndarray:        
                self.band_tags.append( 'sol. azimuth' )
            else:
                self.band_tags.append( 'none' )
            index += 1

        if self.p.readsensor:
            
            self.sink[:,:,index] = mod.readangles( 'SensorZenith' )
            if type( self.sink[:,:,index] ) is np.ndarray:        
               self.band_tags.append( 'sen. zenith' )
            else:
                self.band_tags.append( 'none' )
                     
            index += 1
            self.sink[:,:,index] = mod.readangles( 'SensorAzimuth' )
            if type( self.sink[:,:,index] ) is np.ndarray:        
               self.band_tags.append( 'sen. azimuth' )
            else:
                self.band_tags.append( 'none' )
            
        mod.closefile()

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
    # thread slightly different
    def apply_work( self ):
        
        self.run()          # run the operator

        if type( self.sink ) is not np.ndarray:
            eprint( 'ag_src: sink not set...returning' ) 
            return

        self.areal_index = None # reset areal to center image
 
        '''
        for i in range(0,len(self.attrs)):    # report attributes
            wx.CallAfter( self.messages.append, 
                          self.attrs[i] + '\n' )

        wx.CallAfter( self.messages.append, self.channels + '\n' )
        '''

    def read_params_from_panel( self ):       # scan panel parameters
        
        self.p.bandstr = self.t_bandstr.GetValue()
        self.p.filepath = self.t_filepath.GetValue()
        self.p.readnav = self.c_readnav.GetValue()
        self.p.readsolar = self.c_readsolar.GetValue()
        self.p.readsensor = self.c_readsensor.GetValue()
        
        if self.r_radiance.GetValue():
            self.p.swconv = 0
        if self.r_reflectance.GetValue():
            self.p.swconv = 1

        return True

    def write_params_to_panel( self ):        # write parameters to panel
        
        self.t_bandstr.SetValue( self.p.bandstr )
        self.t_filepath.SetValue( self.p.filepath )
        self.c_readnav.SetValue( self.p.readnav )
        self.c_readsolar.SetValue( self.p.readsolar )
        self.c_readsensor.SetValue( self.p.readsensor )
        
        if  self.p.swconv == 0:
            self.r_radiance.SetValue( True )
        elif  self.p.swconv == 1:
            self.r_reflectance.SetValue( True )

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.c_readnav = wx.CheckBox( self.p_client, -1, 'navigation' )
        self.c_readnav.SetToolTip( 'load navigation data for display' )
        h_sizer.Add( self.c_readnav, 0, wx.ALL, 2 )

        self.c_readsolar = wx.CheckBox( self.p_client, -1, 'solar angles' )
        self.c_readsolar.SetToolTip( 'load solar angles into buffers' )
        h_sizer.Add( self.c_readsolar, 0, wx.ALL, 2 )

        self.c_readsensor = wx.CheckBox( self.p_client, -1, 'sensor angles' )
        self.c_readsensor.SetToolTip( 'load sensor angles into buffers' )
        h_sizer.Add( self.c_readsensor, 0, wx.ALL, 2 )

        self.r_radiance = wx.RadioButton( self.p_client, -1, 'radiance', 
                                          style = wx.RB_GROUP )
        self.r_radiance.SetToolTip( 'use radiance values for shortwave' )
        h_sizer.Add( self.r_radiance )

        self.r_reflectance = wx.RadioButton( self.p_client, -1, 'reflectance' )
        self.r_radiance.SetToolTip( 'use reflectance values for shortwave' )
        h_sizer.Add( self.r_reflectance )

        v_sizer.Add( h_sizer )
        prompt = wx.StaticText( self.p_client, -1, 
                                ' enter channels to read (1-index):' )
        v_sizer.Add( prompt, 0, wx.TOP, 8 ) 

        self.t_bandstr = wx.TextCtrl( self.p_client, -1 )
        self.t_bandstr.SetToolTip( 'comma delimited string eg 1,52,8' )
        #self.t_bandstr.Bind( wx.EVT_KEY_DOWN, self.on_file_key) 
        v_sizer.Add( self.t_bandstr, 1, wx.EXPAND )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 
                                ' enter image filepath:' )
        h_sizer.Add( prompt, 0, wx.TOP, 9 )  # lower prompt

        # browse directory button
        b_browse = wx.Button( self.p_client, -1, 'browse', 
                              (232,79), (60,25) )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        b_browse.SetToolTip( 'browse directory for image file' )

        h_sizer.Add( (1, 1),1 ) # , '1' pushes button to right
        h_sizer.Add( b_browse, 0 )
        v_sizer.Add( h_sizer, 1, wx.EXPAND )

        self.t_filepath = wx.TextCtrl( self.p_client, -1, size=(100,20) )       
        self.t_filepath.SetToolTip( 'enter image filepath' )
        #self.t_filepath.Bind( wx.EVT_KEY_DOWN, self.on_file_key ) 
        dt = FileDrop( self.t_filepath, self )
        self.t_filepath.SetDropTarget( dt )

        v_sizer.Add( self.t_filepath, 1, wx.EXPAND )
        self.p_client.SetSizer( v_sizer )

        self.write_params_to_panel()

    def on_file_drop( self, event ):

        if self.c_apply_on_file_drop.GetValue():
            self.p.apply_on_file_drop = False
        else:
            self.p.apply_on_file_drop = True
  
    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, 'Choose an image to read', 
                             os.getcwd(), "", "*", wx.OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        # TODO: put angle options
        eprint( 'usage: mod02_src' )
        eprint( '       -h, --help' )
        eprint( '       -n, --nav' )
        eprint( '       -c channels, --channels=channels' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( '       -f filepath, --file=filepath' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is filepath, output is stdout' )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hnc:p:f:', 
                                        ['help','nav','channels=', 'param=',
                                         'file='])
        except getopt.GetoptError:           
            self.usage()              
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)
                
            if opt in ( '-n', '--nav' ): 
                self.p.readnav = True
                
            elif opt in ( '-p', '--params' ):
                params = arg
                
            elif opt in ( '-f', '--file' ):
                self.p.filepath = arg
                
            elif opt in ( '-c', '--channels' ):
                self.p.bandstr = arg
                eprint( 'HHHHH', self.p.bandstr )

        if params == None and self.p.filepath == '':
            eprint( 'mod02_src: no filename or parmfile  given...exiting' )
            sys.exit( 2 )
            
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'mod02_src: set_params: bad params file read' )
                eprint( '...exiting' )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':
    
    oper = instantiate()           # source point for pipe
    oper.set_params( sys.argv[1:] )
    oper.run()
    
    oper.sink.dump( sys.stdout.buffer )   # send downstream    
