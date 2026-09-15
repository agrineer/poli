#! /usr/bin/env python

'''
@file projmod_src.py
@author Scott L. Williams
@package POLI
@brief MODIS data source for projected modis data
@LICENSE
#  projmod_src.py

#  Copyright (C) 2010-2026 Scott L. Williams.
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
sections DESCRIPTION
a projected MODIS data source point 
source is calibrated radiometrically and DOES NOT contain geo-referenced
(centered) pixels but can be calculated if given coordinates
'''

projmod_src_copyright = 'projmod_src.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint
from urllib import request

try:
    from projmod_src.projmod_hdf import projmod_hdf # using GUI
    
except:
    from projmod_hdf import projmod_hdf # non-GUI..loads twice due to module name
    eprint( 'projmod_hdf: using non-graphics mode' )

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
    eprint( 'projmod_src: using non-graphics mode.' )
    
def get_name(): 
    return 'projmod_src'

# return an instance of 'projmod_src' class 
def instantiate():	
    return projmod_src( get_name() )

class projmod_src_parameters( pio ):
    
    def __init__( self ):
        
        self.filepath = ''             # input modis file
        self.use_file_cache = False
        self.bandstr = ''              # bands to read in
        self.swconv = 'reflectance'    # shortwave conv:0-radiance 1-reflectance

        self.calc_latlon = False       # calculate coordinates (equirect)

        # values are for outer edge, not center of corner pixel
        # default to SCRB values
        self.tl_lat = 35.0             # top left
        self.tl_lon = -108.0
        self.br_lat = 31.0             # lower right 
        self.br_lon = -104.00

        self.apply_on_file_drop = True

    def print_params( self ):
        
        eprint( '\nparameters for projmod_src:' )
        eprint( '                   filepath =', self.filepath )
        eprint( '             use file cache =', self.use_file_cache )
        eprint( '                band string =', self.bandstr )
        eprint( '             shortwave conv =', self.swconv )
        eprint( '         apply on file drop =', self.apply_on_file_drop )
        eprint( '              calc lat long =', self.calc_latlon )
        eprint( '          top left latitude =', self.tl_lat )
        eprint( '         top left longitude =', self.tl_lon )
        eprint( '         bot right latitude =', self.br_lat )
        eprint( '        bot right longitude =', self.br_lon )        
        
# -------------------------------------------------------------------------

class projmod_src( operator ):         # projected modis source operator
    
    def __init__( self, name ):        # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = projmod_src_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version, '\n' )

    def use_cache( self, mod, cache_path ):
        
        try:
            mod.open_file( cache_path )     
            eprint( 'projmod_src: using cached datafile:', cache_path )
 
        except:
            
            # not there, get and put in cache
            base = os.path.basename( self.p.filepath )
            eprint( 'projmod_src: data file:', base,
                    'not in cache...retrieving' )

            # put in cache to load and for later use if needed
            try:
                eprint( 'projmod_src: getting URL file:', self.p.filepath ) 
                request.urlretrieve( self.p.filepath, cache_path )
                            
            except Exception as e:
                eprint( e )
                eprint( 'projmod_src: check above messages to see' )
                eprint( '             what went wrong...returning' )
                                       
            mod.open_file( cache_path )     
            eprint( 'projmod_src: using fresh URL datafile:', self.p.filepath )
        
    def URLload( self, mod ):
        
        # get environment variables $POLI_HOME, $POLI_USE_CACHE
        POLI_HOME = os.environ['POLI_HOME']
        base = os.path.basename( self.p.filepath )
        cache_dir = POLI_HOME + '/.cache/'
        cache_path = cache_dir + base

        if not os.path.isdir( cache_dir ):
            os.mkdir( cache_dir )  # make directory if not there
 
        if self.p.use_file_cache:
           self.use_cache( mod, cache_path )
                         
        else:                 
            # put in cache to load and for later use if needed
            try:
                eprint( 'projmod_src: getting URL file:', self.p.filepath ) 
                request.urlretrieve( self.p.filepath, cache_path )
                mod.open_file( cache_path )
            
            except Exception as e:
                eprint( str(e) )
                raise OSError( 'projmod_src: URLload: bad url retrieval' )

    def str2tuple(self, s):

        # check for dangling ','
        if s[-1] == ',':
            s = s[:-1]
 
        items = s.split(',')           # convert tuple-like strings 
                                       # to real tuples.
                                       # eg '1,2,3,4' -> (1, 2, 3, 4)
        t = [x.strip() for x in items] # clean up spaces
        return tuple( t )

    def run( self ):
        
        self.p.print_params()   # report parameters used when running
        self.print_versions()

        if self.p.bandstr == '':
            eprint( 'projmod_src: run: band string is empty...returning' )
            return
         
        mod = projmod_hdf()

        try:
            if self.p.filepath[:4] == 'http':
                self.URLload( mod )  

            else:
                
                eprint( 'projmod_src: getting local file:', self.p.filepath )
                mod.open_file( self.p.filepath ) 
              
                if mod.hdf_sd == None:
                    eprint( 'projmod_src: cannot open file:' + self.p.filepath )
                    self.sink = None
                    return

        except OSError as e:
            eprint( e )
            eprint( 'projmod_src: cannot open file: ' + self.p.filepath )
            self.sink = None
            return

        mod.read_attributes()          # get modis type, sets sizes

        stuple = self.str2tuple( self.p.bandstr )
        nbuf = len( stuple )
        self.sink = np.empty( (mod.height,mod.width,nbuf),
                              dtype=np.float32 )
        self.sink.fill( np.nan )       # fill miss-read buffers with nans

        index = 0
        self.band_tags = []

        for i in stuple:
            
            band,tag = mod.readband( i, self.p.swconv )
            
            #if type( band ) is np.ndarray:
            if isinstance( band, np.ndarray ):
                self.sink[:,:,index] = band
                self.band_tags.append( tag )
            else:
                self.band_tags.append( 'none' )
                
            index += 1

        if self.p.calc_latlon:   # load nav angles

            self.nav_data = mod.make_latlon( self.p.tl_lat, 
                                             self.p.tl_lon,
                                             self.p.br_lat, 
                                             self.p.br_lon )      
            self.nav_tags = ['lat', 'lon']
            self.sink = np.append( self.sink, self.nav_data, 2 )
            self.band_tags.append( 'latitude' )
            self.band_tags.append( 'longitude' )
            
        else:
            self.nav_data = None
            self.nav_tags = None

        mod.close_file()

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
        
        #if type( self.sink ) is not np.ndarray:
        if not isinstance( self.sink, np.ndarray ):
            eprint( 'ag_src: sink not set...returning' ) 
            return

        self.areal_index = None # reset areal to center image
 
        '''
        for i in range( 0,len(self.attrs)):    # report attributes
            wx.CallAfter( self.messages.append, 
                          self.attrs[i] + '\n' )

        wx.CallAfter( self.messages.append, self.channels + '\n' )
        '''
    def read_params_from_panel( self ):       # scan panel parameters

        self.p.bandstr = self.t_bandstr.GetValue().strip()
        self.p.filepath = self.t_filepath.GetValue().strip()
        self.p.calc_latlon = self.c_calc_latlon.GetValue()
        self.p.use_file_cache = self.c_use_file_cache.GetValue()
        
        if self.r_radiance.GetValue():
            self.p.swconv = 'radiance'
        if self.r_reflectance.GetValue():
            self.p.swconv = 'reflectance'

        self.p.c_calc_latlon = self.c_calc_latlon.GetValue()
        self.p.tl_lat = float( self.t_tl_lat.GetValue().strip() )
        self.p.tl_lon = float( self.t_tl_lon.GetValue().strip() )
        self.p.br_lat = float( self.t_br_lat.GetValue().strip() )
        self.p.br_lon = float( self.t_br_lon.GetValue().strip() )

        self.p.apply_on_file_drop = self.c_apply_on_file_drop.GetValue()

        return True

    def write_params_to_panel( self ):        # write parameters to panel
        
        self.t_bandstr.SetValue( self.p.bandstr )
        self.t_filepath.SetValue( self.p.filepath )
        
        if self.p.swconv == 'radiance':
            self.r_radiance.SetValue( True )
        elif self.p.swconv == 'reflectance':
            self.r_reflectance.SetValue( True )

        self.c_calc_latlon.SetValue( self.p.calc_latlon )
        
        self.t_tl_lat.SetValue( '%8.3f'%self.p.tl_lat )
        self.t_tl_lon.SetValue( '%8.3f'%self.p.tl_lon )
        self.t_br_lat.SetValue( '%8.3f'%self.p.br_lat )
        self.t_br_lon.SetValue( '%8.3f'%self.p.br_lon )

        self.c_apply_on_file_drop.SetValue( self.p.apply_on_file_drop )
        self.c_use_file_cache.SetValue( self.p.use_file_cache )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.r_radiance = wx.RadioButton( self.p_client, -1, 'radiance', 
                                          style = wx.RB_GROUP )
        self.r_radiance.SetToolTip( 'use radiance values for shortwave' )
        h_sizer.Add( self.r_radiance )

        self.r_reflectance = wx.RadioButton( self.p_client, -1, 'reflectance' )
        self.r_radiance.SetToolTip( 'use reflectance values for shortwave' )
        h_sizer.Add( self.r_reflectance )

        v_sizer.Add( h_sizer )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
   
        self.c_apply_on_file_drop = wx.CheckBox( self.p_client, -1,
                                                 'apply on file drop' )
        self.c_apply_on_file_drop.SetToolTip( 'immediate execution when file is dropped or double clicking the data file in data suites' )

        self.c_apply_on_file_drop.Bind( wx.EVT_LEFT_UP, self.on_file_drop )
        h_sizer.Add( self.c_apply_on_file_drop )

        self.c_use_file_cache = wx.CheckBox( self.p_client, -1,'use file cache')
        self.c_use_file_cache.SetToolTip( 'use local caching rather than from a URL' )
        h_sizer.Add( self.c_use_file_cache )
  
        v_sizer.Add( h_sizer )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.c_calc_latlon = wx.CheckBox( self.p_client, -1, 'calc. lat/lon')
        self.c_calc_latlon.SetToolTip( 'calculate coordinates' )
        h_sizer.Add( self.c_calc_latlon )

        prompt = wx.StaticText( self.p_client, -1, 
                                '      top left, bottom right lat/lon:' )
        h_sizer.Add( prompt, 0, wx.TOP, 2 )
        h_sizer.Add( 10, 1 )
        self.t_tl_lat = wx.TextCtrl( self.p_client, -1, '', size=(60,20),
                                     style=wx.ALIGN_RIGHT )
        self.t_tl_lat.SetToolTip( 'top left lat' )
        h_sizer.Add( self.t_tl_lat )
        h_sizer.Add( 10, 1 )

        self.t_tl_lon = wx.TextCtrl( self.p_client, -1, '', size=(60,20),
                                     style=wx.ALIGN_RIGHT )

        self.t_tl_lon.SetToolTip( 'top left lon' )
        h_sizer.Add( self.t_tl_lon )
        h_sizer.Add( 10, 1 )

        self.t_br_lat = wx.TextCtrl( self.p_client, -1, '', size=(60,20),
                                     style=wx.ALIGN_RIGHT )

        self.t_br_lat.SetToolTip( 'bottom right lat' )
        h_sizer.Add( self.t_br_lat )
        h_sizer.Add( 10, 1 )

        self.t_br_lon = wx.TextCtrl( self.p_client, -1, '', size=(60,20),
                                     style=wx.ALIGN_RIGHT )

        self.t_br_lon.SetToolTip( 'bottom right lon' )
        h_sizer.Add( self.t_br_lon )
        h_sizer.Add( 10, 1 )

        v_sizer.Add( h_sizer )

        prompt = wx.StaticText( self.p_client, -1, 
                                ' enter bands to read (1-index):' )
        v_sizer.Add( prompt ) 

        self.t_bandstr = wx.TextCtrl( self.p_client, -1 )
        self.t_bandstr.SetToolTip( 'comma delimited string eg 1,52,8' )
        v_sizer.Add( self.t_bandstr, 1, wx.EXPAND )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 
                                ' enter modis filepath:' )
        h_sizer.Add( prompt )  # lower prompt
        v_sizer.Add( h_sizer )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.t_filepath = wx.TextCtrl( self.p_client, -1 )       
        self.t_filepath.SetToolTip( 'enter image filepath' )
        dt = FileDrop( self.t_filepath, self )
        self.t_filepath.SetDropTarget( dt )

        h_sizer.Add( self.t_filepath, 1, wx.EXPAND )

        # browse directory button
        b_browse = wx.Button( self.p_client, -1, 'browse', size=(60,25) )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        b_browse.SetToolTip( 'browse directory for image file' )

        h_sizer.Add( b_browse, 0 )

        v_sizer.Add( h_sizer, 1, wx.EXPAND )
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
                             os.getcwd(), "", "*", wx.FD_OPEN )

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
        eprint( 'usage: projmod_src.py' )
        eprint( '      -h, --help' )
        eprint( '      -c, --cache' )
        eprint( '      -n, --nav   flag to calculate lat lon' )
        eprint( '      -s <radiance,refectance>' )
        eprint( '      --swconv=<radiance,reflectance>' )
        eprint( '      -b strbands, --bands=strbands' )
        eprint( '      -f filepath, --file=filepath' )
        eprint( '      -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is filepath, output is stdout' )

    def set_params( self, argv ):
                
        params = None
 
        try:                                
            opts, args = getopt.getopt( argv,
                                        'hcns:b:f:p:', 
                                        ['help','nav','swconv=','bands=',
                                         'file=','cache','param='] )
        except getopt.GetoptError as e:
            eprint( 'proj_src: ' + str(e) )  
            self.usage()              
            sys.exit(2)  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)

            elif opt in ( '-c', '--cache' ):      
                self.p.use_file_cache = True

            elif opt in ( '-n', '--cnav' ):      
                self.p.calc_latlo = True
 
            elif opt in ( 's', '--swconv' ):
                
                if arg not in ( 'radiance', 'reflectance' ):
                    eprint( 'projmod: unknown option for swconv:',
                            arg, ' ...exiting' )
                    sys.exit( 2 )
                self.p.swconv = arg
                
            elif opt in ( '-b', '--bands' ):
                self.p.bandstr = arg

            elif opt in ( '-f', '--file' ):
                self.p.filepath = arg         
              
            elif opt in ( '-p', '--params' ):
                params = arg

        if self.p.bandstr == '':
           eprint( 'projmod_src: bandstr not given...exiting' )
           sys.exit( 2 )
  
        if params == None and self.p.filepath == '':
            eprint( 'projmod_src: no filename or paramfile given...exiting' )
            sys.exit( 2 )

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'projmod_src: set_params: bad params file read' )
                eprint( '...exiting' )
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
