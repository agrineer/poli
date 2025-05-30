#! /usr/bin/env python3

'''
@file wrf_sr c.py
@author Scott L. Williams
@package POLI
@brief A netCDF wrf data source POLI operator.
@LICENSE
#
#  wrf_src.py Copyright (C) 2016-2025 Scott L. Williams.
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
netCDF wrf data source
XLAT and XLONG can be appended to buffers
'''
wrf_src_copyright = 'wrf_src.py Copyright (c) 2016-2025 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import netCDF4
import numpy as np
from pio import pio
from urllib import request
from ezprint import eprint

# determine if graphics (wx.python) can be enabled
try:
    import wx
    from op_panel import op_panel
    from filedrop import FileDrop
    operator = op_panel                # uses op_panel in command line
                                       # or batch mode when wx is available
           
# if not then assume non-graphics implementation
except:   
    from op import op
    operator = op
    eprint( 'wrf_src: using non-graphics mode' )

def get_name(): 
    return 'wrf_src'

# return an instance of 'wrf_src' class 
def instantiate():	
    return wrf_src( get_name() )

class wrf_src_parameters( pio ):
    
    def __init__( self ):
        
        self.filepath = ''      # input netcdf file
        self.bandstr = ''       # bands to read in given as string
        '''
        self.tslice_band = -1.0 # if > -1.0 add band with that constant values.
                                # workaround for time input in SOM mplementation
        
                                # FIXME: hidden feature as it does not have a
                                # gui or command line parameter. consider making
                                # just a constant band with negative values
        '''
        self.apply_on_file_drop = True
        self.append_nav = False
        self.use_file_cache = False

    def print_params( self ):
        
        eprint( '\nparameters for wrf_src:' )
        eprint( '              filepath =', self.filepath )
        eprint( '              band str =', self.bandstr )
        eprint( '        append lat/lon =', self.append_nav )                   
        eprint( '        use_file_cache =', self.use_file_cache )
        eprint( '    apply on file drop =', self.apply_on_file_drop )
    
# ------------------------------------------------------------------------
 
class wrf_src( operator ):             # wrf netcdf source operator

    def __init__( self, name ):        # initialize operator but no graphics
        
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = wrf_src_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '     ', self.name,'=', self.__version__ )
        eprint( '        numpy =', np.version.version )
        eprint( '      netCDF4 =', netCDF4.__version__ )

    def use_cache( self, cache_path ):
        
        try:
             # open the netcdf file
            ds = netCDF4.Dataset(  cache_path, 'r' ) 
            eprint( 'wrf_src: using cached datafile:', cache_path )
            
        except:
            
            # not there, get and put in cache
            base = os.path.basename( self.p.filepath ) 
            eprint( 'wrf_src: data file:', base,
                    'not in cache...retrieving' )

            # put in cache to load and for later use if needed
            try:
                eprint( 'wrf_src: getting URL file:', self.p.filepath ) 
                request.urlretrieve( self.p.filepath, cache_path )
                            
            except Exception as e:
                
                eprint( e )
                eprint( 'wrf_src: check above messages to see' )
                eprint( '         what went wrong' )
                raise Error( 'wrf_src: unable to url retrieve' )

            ds = netCDF4.Dataset(  cache_path, 'r' )                     
            eprint( 'wrf_src: using fresh URL datafile:', self.p.filepath )
            
        return ds
     
    def URLload( self ):
        
        # get environment variables $POLI_HOME, $POLI_USE_CACHE
        POLI_HOME = os.environ['POLI_HOME']
        base = os.path.basename( self.p.filepath )
        cache_dir = POLI_HOME + '/.cache/'
        cache_path = cache_dir + base

        if not os.path.isdir( cache_dir ):
            os.mkdir( cache_dir )  # make directory if not there
 
        if self.p.use_file_cache:
            ds = self.use_cache( cache_path )
                         
        else:
                    
            # put in cache for later use if needed
            eprint( 'wrf_src: getting URL file:', self.p.filepath )
            try:
                request.urlretrieve( self.p.filepath, cache_path )
                ds = netCDF4.Dataset(  cache_path, 'r' )
 
            except Exception as e:
                eprint( str(e) )
                raise Error( 'wrf_src: URLload: bad url retrieval' )
        
        return ds

    # parses out variable time slice, and if 4D, the level
    def str2list( self, s ): 

        self.buf = []                 # buffer variable name
        self.tband = []               # time bands
        self.lband = []               # level bands

        s = s.strip()                 # remove trailing white space
        
        # check for dangling ','
        if s[-1] == ',':
            s = s[:-1]
        items = s.split(',')          

        u = [ x.replace(' ', '') for x in items ] # clean up spaces
        
        self.nbuf = len( u )          # initiakl parse for nbuf

        # parse out time and level slices
        for x in u:
            
            items = x.split(':')
            self.buf.append( items[0] )
            self.tband.append( int(items[1]) )

            # determine if 4D
            try:
                self.lband.append( int(items[2]) ) # get level here
            except:
                self.lband.append( None )
    
    def run( self ):                   # override superclass run

        self.p.print_params()          # report parameters used
        self.print_versions()

        try:
            if self.p.filepath[:4] == 'http':
                self.ds = self.URLload()
            else:
                # local filepath
                eprint( 'wrf_src: getting local file:', self.p.filepath )
                
                # open the netcdf file
                self.ds = netCDF4.Dataset(  self.p.filepath, 'r' ) 
 
        except OSError as e:
            
            eprint( str(e) )
            eprint( 'wrf_src: cannot open file:', self.p.filepath )
            self.sink = None
            return

        try:           
            self.str2list( self.p.bandstr )
            
        except:
            eprint( 'wrf_src: run: invalid buffer string...returning' )
            return
        
        # grab data from wrf output
        for i in range( 0, self.nbuf ):

            try:
                if self.lband[i] == None:
                    data = self.ds.variables[ self.buf[i] ][ self.tband[i] ]
                else:
                    # extract from 4-D buffer (eg.atmospheric levels)
                    data = self.ds.variables[self.buf[i]][self.tband[i]][self.lband[i]]
            except:
                eprint( 'wrf_src:: could not read buffer:', self.buf[i],
                        'returning' )
                return

            if i == 0:
                
                # make output buffer now that we have the info
                ny,nx = data.shape
                if self.p.append_nav:
                    nbuf = self.nbuf + 2
                else:
                    nbuf = self.nbuf
                temp = np.empty( (ny, nx, nbuf), dtype=data.dtype )

            temp[:,:,i] = data

        if self.p.append_nav:
            temp[:,:,nbuf-2] = self.ds.variables['XLAT'][0]
            temp[:,:,nbuf-1] = self.ds.variables['XLONG'][0]
            
        self.sink = np.flip( temp, 0 ) # netCDF4 gives upside down data
         
    ####################################################################
    # gui section
    ####################################################################

    def set_filepath( self, obj ):
        
        if isinstance( obj, str ):             # we've been invoked by
            obj.strip()                        # image_tree or file drop
            self.t_filepath.SetValue( obj )
            
        if self.p.apply_on_file_drop:
            self.on_apply( None )

    # override since we are a source
    def apply_work( self ):
        
        self.run()          # run the operator

        # check if valid run output
        if not isinstance( self.sink, np.ndarray ):
            eprint( 'wrf_src: run output buffer not valid...returning' )
            return

        self.areal_index = None # reset areal to center image

        # construct buffer tags
        self.band_tags = []
        for i in range( 0, self.nbuf ):
            
            tag = self.buf[i] + ':' + str( self.tband[i] )
            if self.lband[i] != None:
                tag = tag + ':' + str( self.lband[i] )
            self.band_tags.append( tag )

        if self.p.append_nav:
            self.band_tags.append( 'lat' )
            self.band_tags.append( 'lon' )

        # set up graphics lat/long report  (a fuerzas)

        numy, numx, nbands = self.sink.shape
        dtype = self.sink.dtype
        self.nav_data = np.empty( (numy,numx,2), dtype=dtype )
        
        # read lat,long buffers
        # NOTE: wrf output files imbed lat/long in each time slice
        #       and so even the filtered version of the output
        #       will contain lat/long buffers, in order to behave as the
        #       original (unfiltered) wrf sources
        #
        # REMINDER: netCDF4 read files have different origin than GDAL
        #           could be a flag somewhere, in the meantime flip them in Y
        self.nav_data[:,:,0] = np.flip( self.ds.variables['XLAT'][0],  0 )
        self.nav_data[:,:,1] = np.flip( self.ds.variables['XLONG'][0], 0 )
        self.nav_tags = ['lat','lon']
        
    def read_params_from_panel( self ):         # scan panel parameters

        filepath = self.t_filepath.GetValue().strip()
        '''
        if not os.path.isfile( filepath ):
            eprint( 'wrf_src: read_params_from_panel:' )
            eprint( '         file cannot be found:', filepath )
            eprint( '         ...returning' )
            return False
        '''
        self.p.filepath = filepath 
 
        self.p.bandstr = self.t_bandstr.GetValue().strip()
        
        self.p.apply_on_file_drop = self.c_apply_on_file_drop.GetValue()
        self.p.append_nav = self.c_append_nav.GetValue()

        self.p.use_file_cache = self.c_use_file_cache.GetValue()

        return True

    def write_params_to_panel( self ):        # write parameters to panel
        
        self.t_bandstr.SetValue( self.p.bandstr )
        self.t_filepath.SetValue( self.p.filepath )
        self.c_apply_on_file_drop.SetValue( self.p.apply_on_file_drop )
        self.c_append_nav.SetValue( self.p.append_nav )
        self.c_use_file_cache.SetValue( self.p.use_file_cache )

    # initialize graphics
    def init_panel( self, benchtop ):

        operator.init_panel( self, benchtop ) # start with basics
            
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.AddSpacer( 2 ) # space from top

        # make checkbox panel
        panel = self.checkboxes_panel()
        v_sizer.Add( panel )
        v_sizer.AddSpacer( 2 )  # add space

        panel = self.bands_panel()
        v_sizer.Add( panel, 1, wx.EXPAND )
        v_sizer.AddSpacer( 2 )  # add space

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
        h_sizer.AddSpacer( 10 ) # spacer from left

        # file input text control
        prompt = wx.StaticText( p_filepath, -1, 'enter WRF file:          ' )
        h_sizer.Add( prompt )
        
        self.t_filepath = wx.TextCtrl( p_filepath, -1, '' )
        self.t_filepath.SetToolTip( 'enter filepath' )
        dt = FileDrop( self.t_filepath, self )
        self.t_filepath.SetDropTarget( dt )

        h_sizer.Add( self.t_filepath, 1, wx.EXPAND )
        h_sizer.AddSpacer( 3 )
        
        b_browse = wx.Button( p_filepath, -1, 'browse' )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )

        h_sizer.Add( b_browse )
        
        p_filepath.SetSizer( h_sizer )
        return p_filepath

    # make text panel
    def bands_panel( self ):
        
        p_bands = wx.Panel( self.p_client, -1 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.AddSpacer( 10 ) # spacer from left

        # file input text control
        prompt = wx.StaticText( p_bands, -1, 'enter band string:' )
        h_sizer.Add( prompt )
        h_sizer.AddSpacer( 10 )
        
        self.t_bandstr = wx.TextCtrl( p_bands, -1 )
        self.t_bandstr.SetToolTip( 'comma delimited string for buffers;' +
                                   ' semi-colon delimited for time and' +
                                   ' level indices. eg T2:20 gives 20th' +
                                   ' time-step T2 band; eg. P:4:20 gives' +
                                   ' pressure at 4th time-step and 20th' +
                                   ' height level. NOTE: 0 indexed' )
        
        h_sizer.Add( self.t_bandstr, 1, wx.EXPAND )

        p_bands.SetSizer( h_sizer )
        return p_bands

    # make checkboxes panel
    def checkboxes_panel( self ):
        
        p_checkboxes = wx.Panel( self.p_client, -1 )

        v_sizer = wx.BoxSizer( wx.VERTICAL )

        # use file cache
        self.c_use_file_cache = wx.CheckBox( p_checkboxes, -1, 'use file cache')
        self.c_use_file_cache.SetToolTip( 'enables/disables use of a cached' +
                                          ' file')
        v_sizer.Add( self.c_use_file_cache )
        v_sizer.AddSpacer( 2 ) 
        
        # file drop
        self.c_apply_on_file_drop = wx.CheckBox( p_checkboxes, -1,
                                                 'apply on file drop' )
        self.c_apply_on_file_drop.SetToolTip( 'immediate execution when file' +
                                              ' is dropped or by double' +
                                              ' clicking the data file in' +
                                              ' data suites' )
        
        self.c_apply_on_file_drop.Bind( wx.EVT_LEFT_UP, self.on_file_drop )
        v_sizer.Add( self.c_apply_on_file_drop )
        v_sizer.AddSpacer( 2 )  # add space

        # append lat/lon
        self.c_append_nav = wx.CheckBox( p_checkboxes, -1,
                                         'append lat/lon buffers' )
        v_sizer.Add( self.c_append_nav )
        
        p_checkboxes.SetSizer( v_sizer )
        return p_checkboxes 

    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, 'Choose an image to read', 
                             os.getcwd(), "", "*", wx.OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

    def on_file_drop( self, event ):
        
        if self.c_apply_on_file_drop.GetValue():
            self.p.apply_on_file_drop = False
        else:
            self.p.apply_on_file_drop = True
     
    ############################################################
    # command line options
    ############################################################

    def usage( self ):

        eprint( '\nusage: wrf_src.py' )
        eprint( '       -h, --help' )
        eprint( '       -n, --nav includes lat,lon buffers')
        eprint( '       -b bands, --bands=bands w/bands as string' )
        eprint( '       -f in_wrf_filepath, --file=in_wrf_filepath' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hnb:f:p:', 
                                        ['help','nav','bands=', 'file=', 'params='])
        except getopt.GetoptError as e:
            eprint( 'wrf_src: ' + str(e) )
            self.usage()              
            sys.exit( 2 )  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            elif opt in ( '-n', '--nav' ):
                self.p.append_nav = True
 
            elif opt in ( '-f', '--file' ):
                self.p.filepath = arg
                
            elif opt in ( '-b', '--bands' ):
                self.p.bandstr = arg
                
            elif opt in ( '-p', '--params' ):
                params = arg  

        if self.p.bandstr == '' and params == None:
            eprint( 'wrf_src: set_params: no band string given' )
            self.usage()
            sys.exit( 2 )
            
        if self.p.filepath == '' and params == None:    
            eprint( 'wrf_src: set_params: no input filename given' )
            self.usage()
            sys.exit( 2 )

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'wrf_src: set_params: bad params file read' )
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


