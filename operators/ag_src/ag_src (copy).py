#! /usr/bin/env python3

'''
@file ag_src.py
@author Scott L. Williams.
@package POLI
@brief AVHRR or GVISSR data source
@LICENSE
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
sections DESCRIPTION
create an AVHRR or GVISSR data source point 
from CoastWatch HDF files for the poli operator chain.
source is assumed to be calibrated radiometrically and 
contains geo-referenced (centered) pixels. 

'''

ag_src_copyright = 'ag_src.py Copyright (c) 2010-2025 Scott L. Williams,' + \
                   ' released under GNU GPL V3.0'
import os
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint
from urllib import request

try:   
    from ag_src.ag_hdf import ag_hdf  # using GUI
    
except:
    from ag_hdf import ag_hdf         # non-GUI..loads twice due to module name
    eprint( 'ag_hdf: using non-graphics mode' )
    
# determine if graphics can be enabled
try:
    import wx
    from filedrop import FileDrop
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
                
# if not, then assume batch or command line implementaion
except Exception as e:
    eprint( 'LOAD:', str( e ) )
    from op import op
    operator = op
    eprint( 'ag_src: using non-graphics mode.' )

def get_name(): 
    return 'ag_src'

# return an instance of 'ag_src' class 
def instantiate():	
    return ag_src( get_name() )

class ag_src_parameters( pio ):
    
    def __init__( self ):
        
        self.filepath = ''           # input coastwatch file
        self.navbuffer = True        # show navigation as buffers
        self.readangles = False      # read sat,sun, rel az angles into buffers

        '''
        self.setgrid = True           # overlay options
        self.setcoast = True
        self.setboundaries = True
        '''
        self.apply_on_file_drop = True

    def print_params( self ):
        
        eprint( '\nparameters for ag_src:' )
        eprint( '    filepath           =', self.filepath )
        eprint( '    navbuffer          =', self.navbuffer )
        eprint( '    readangles         =', self.readangles )
        '''
        eprint( '    setgrid            =', self.setgrid )
        eprint( '    setcoast           =', self.setcoast )
        eprint( '    setboundaries      =', self.setboundaries )
        '''
        eprint( '    apply on file drop =', self.apply_on_file_drop )
       
# ----------------------------------------------------------------------------
    
class ag_src( operator ):             # coastwatch image source operator
    
    def __init__( self, name ):       # initialize op_panel but no graphics

        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = ag_src_parameters()

    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
 
    def use_cache( self, ag, cache_path ):
        
        try:
            ag.open_file( cache_path )     
            eprint( 'ag_src: using cached datafile:', cache_path )
 
        except:
            
            # not there, get and put in cache
            base = os.path.basename( self.p.filepath )
            eprint( 'ag_src: data file:', base,
                    'not in cache...retrieving' )

            # put in cache to load and for later use if needed
            try:
                eprint( 'ag_src: getting URL file:', self.p.filepath ) 
                request.urlretrieve( self.p.filepath, cache_path )
                            
            except Exception as e:
                eprint( e )
                eprint( 'ag_src: check above messages to see' )
                eprint( '         what went wrong...returning' )
                                       
            ag.open_file( cache_path )     
            eprint( 'ag_src: using fresh URL datafile:', self.p.filepath )
        
    def URLload( self, ag ):
        
        # get environment variables $POLI_HOME, $POLI_USE_CACHE
        POLI_HOME = os.environ['POLI_HOME']
        base = os.path.basename( self.p.filepath )
        cache_dir = POLI_HOME + '/.cache/'
        cache_path = cache_dir + base

        if not os.path.isdir( cache_dir ):
            os.mkdir( cache_dir )  # make directory if not there
 
        POLI_USE_CACHE = os.environ['POLI_USE_CACHE']
        eprint( 'ag_src: POLI_USE_CACHE=', POLI_USE_CACHE )
 
        if POLI_USE_CACHE in [ 'YES','Yes','Y','yes','y']:
            self.use_cache( ag, cache_path )
                         
        elif POLI_USE_CACHE in [ 'NO','No','N','no','n']:
                    
            # put in cache to load and for later use if needed
            eprint( 'ag_src: getting URL file:', self.p.filepath ) 
            request.urlretrieve( self.p.filepath, cache_path )
            ag.open_file( cache_path )     
 
        else:
            eprint( 'ag_src:  bad value for environment variable:' )
            eprint( '         POLI_USE_CACHE=', POLI_USE_CACHE )
            eprint( '         use one of yes, no, y, n' )
            eprint( '         returning....' )
            raise Error( 'bad environment variable' )
        
    def run( self ):                         

        self.p.print_params()   # report parameters used when running
        self.print_versions()

        ag = ag_hdf()

        try:
            if self.p.filepath[:4] == 'http':
                self.URLload( ag )  

            else:
                
                eprint( 'ag_src: getting local file:', self.p.filepath )
                ag.open_file( self.p.filepath )      
              
                if ag.hdf_sd == None:
                    eprint( 'ag_src: cannot open file:' + self.p.filepath )
                    self.sink = None
                    return

        except OSError as e:
            eprint( e )
            eprint( 'ag_src: cannot open file: ' + self.p.filepath )
            self.sink = None
            return

        ag.determine_type()                  # determine if avhrr or gvissr
        self.sink = ag.read_spectrum()       # read spectral bands
        self.attr = ag.attr                  # pass along sat attributes
        self.attr_report = ag.format_attributes() # report attr string

        # set band names; ignored if non-gui
        self.band_tags = ag.bands            
        self.channels = ag.channels

        '''
        self.timestamp = ag.pass_date + ag.start_time/86400.0 # fractional day
        '''

        self.nav_data = ag.read_navigation()      # load nav angles
        self.nav_tags = ['lat', 'lon']

        if self.p.navbuffer:
            
            height,width,nbands = self.sink.shape # expand and append buffers
            temp = np.empty((height,width,nbands+2), self.sink.dtype )
            
            for i in range(0,nbands):
                temp[:,:,i] = self.sink[:,:,i]
                
            temp[:,:,nbands] = self.nav_data[:,:,0]
            temp[:,:,nbands+1] = self.nav_data[:,:,1]
            
            self.sink = temp
            self.band_tags.append( 'lat' )
            self.band_tags.append( 'long' )

        if self.p.readangles:                     # sat,sun zenith angles
                                                  # rel,sat azimuth angles
            height,width,nbands = self.sink.shape # expand and append buffers
            temp = np.empty((height,width,nbands+4), self.sink.dtype )
            
            for i in range(0,nbands):
                temp[:,:,i] = self.sink[:,:,i]
            
            self.angles = ag.read_angles()           # snag angles
            temp[:,:,nbands]   = self.angles[:,:,0]  # angles get passed along
            temp[:,:,nbands+1] = self.angles[:,:,1]  # in op_panel
            temp[:,:,nbands+2] = self.angles[:,:,2]
            temp[:,:,nbands+3] = self.angles[:,:,3]

            self.sink = temp

            self.band_tags.append( 'satzen' )
            self.band_tags.append( 'sunzen' )
            self.band_tags.append( 'relaz' )
            self.band_tags.append( 'sataz' )

        #self.overlay = self.ag.read_overlay()
        ag.close_file()

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
    # thread slightly different; called from app thread
    def apply_work( self ):
        
        self.run()          # run the operator

         # check if valid run output
        if type( self.sink ) is not np.ndarray:
            eprint( 'ag_src: sink not set...returning' )
            return

        self.areal_index = None # reset areal to center image
 
        for i in range( 0 ,len(self.attr_report) ):    # report attributes
            wx.CallAfter( self.messages.append, 
                          self.attr_report[i] + '\n' )

        wx.CallAfter( self.messages.append, self.channels + '\n' )

        '''
	# get overlays for display purposes
        if self.p.setgrid == True or \
           self.p.setcoast == True or \
           self.p.setboundaries == True:

            ag = ag_hdf()
            self.overlay_image = ag.make_overlay_image( self.overlay,
                                                        self.p.setgrid,
                                                        self.p.setcoast,
                                                        self.p.setboundaries )
        '''

    def read_params_from_panel( self ):       # scan panel parameters
        
        self.p.filepath = self.t_filepath.GetValue().strip()
        self.p.navbuffer = self.c_navbuffer.GetValue()
        self.p.readangles = self.c_readangles.GetValue()
        self.p.apply_on_file_drop = self.c_apply_on_file_drop.GetValue()
        '''
        self.p.setgrid = self.c_setgrid.GetValue()
        self.p.setcoast = self.c_setcoast.GetValue()
        self.p.setboundaries = self.c_setboundaries.GetValue()
        '''
        return True
    
    def write_params_to_panel( self ):        # write parameters to panel
        
        self.t_filepath.SetValue( self.p.filepath )
        self.c_navbuffer.SetValue( self.p.navbuffer )
        self.c_readangles.SetValue( self.p.readangles )
        self.c_apply_on_file_drop.SetValue( self.p.apply_on_file_drop )
        '''
        self.c_setgrid.SetValue( self.p.setgrid )
        self.c_setcoast.SetValue( self.p.setcoast )
        self.c_setboundaries.SetValue( self.p.setboundaries )
        '''

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1, 10 )
        
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        self.c_readangles = wx.CheckBox( self.p_client, -1,
                                         'load angles into buffers' )
        self.c_readangles.SetToolTip( 'loads sat,sun zenith and rel az angles into buffers' )
        h_sizer.Add( self.c_readangles )
        h_sizer.Add( 10, 1 )
        
        self.c_navbuffer = wx.CheckBox( self.p_client, -1,
                                        'load nav into buffers' )       
        self.c_navbuffer.SetToolTip( 'loads navigation data into buffers' )
        h_sizer.Add( self.c_navbuffer )
        h_sizer.Add( 10, 1 )

        self.c_apply_on_file_drop = wx.CheckBox( self.p_client, -1,
                                                 'apply on file drop' )
        self.c_apply_on_file_drop.SetToolTip( 'immediate execution when file is dropped or double clicking the data file in data suites' )

        self.c_apply_on_file_drop.Bind( wx.EVT_LEFT_UP, self.on_file_drop )
        h_sizer.Add( self.c_apply_on_file_drop )
        v_sizer.Add( h_sizer )
        v_sizer.Add( 1, 10 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
 
        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 'enter image filepath:' )
        h_sizer.Add( prompt )

        # browse directory button
        b_browse = wx.Button( self.p_client, -1, 'browse', (232,79), (60,25) )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        b_browse.SetToolTip( 'browse directory for image file' )

        h_sizer.Add( (1, 1),1 ) # '1' pushes button to right

        h_sizer.Add( b_browse )
        v_sizer.Add( h_sizer,1, wx.EXPAND )
        
        self.t_filepath = wx.TextCtrl( self.p_client, -1 )       
        self.t_filepath.SetToolTip( 'enter image filepath' )
        #self.t_filepath.Bind( wx.EVT_KEY_DOWN, self.on_file_key ) 
        dt = FileDrop( self.t_filepath, self )
        self.t_filepath.SetDropTarget( dt )

        v_sizer.Add( self.t_filepath, 1, wx.EXPAND )
        self.p_client.SetSizer( v_sizer )

        self.write_params_to_panel()

    '''
    # intercept keystroke; look for CR
    def on_file_key( self, event ):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:   
            self.on_apply( None )    # as if pressing 'apply' button
        event.Skip()                 # pass along event
    '''

    def on_file_drop( self, event ):
        
        if self.c_apply_on_file_drop.GetValue():
            self.p.apply_on_file_drop = False
        else:
            self.p.apply_on_file_drop = True
    
    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, "Choose an image to read", 
                             os.getcwd(), "", "*", wx.OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

    ############################################################
    # command line options
    ############################################################

    # TODO: update params stuff
    def usage( self ):
        eprint( 'usage: ag_src' )
        eprint( '       -h, --help' )
        eprint( '       -n, --nav' )
        eprint( '       -f filepath, --file=filepath' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is filepath, output is stdout' )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hn:p:f:', 
                                        ['help','nav','params=','file='])
        except getopt.GetoptError:           
            self.usage()              
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)
                
            elif opt in ( '-n', '--nav' ):
                self.p.navbuffer = True
                
            elif opt in ( '-f', '--file' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'ag_src: file:', arg, ' cannot be found...exiting')
                    sys.exit( 2 )
                self.p.filepath = arg
                
            elif opt in ( '-p', '--params' ):
                params = arg  
 
        if params == None and self.p.filepath == '':
            eprint( 'ag_src: no filename given...exiting' )
            sys.exit( 2 )

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'ag_src:set_params: bad params file read' )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':

    oper = instantiate()           # source point for pipe
    oper.set_params( sys.argv[1:] )
    oper.run()            
    oper.sink.dump( sys.stdout.buffer )   # send downstream    
