'''
@file op_panel.py
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
op_panel_copyright = 'op_panel.py Copyright (c) 2010-2025 Scott L. Williams, released under GNU GPL V3.0'

import os
import wx
import sys
import time
import pickle

from op import op
import numpy as np
from PIL import Image	
from ezprint import eprint

from threads import apply_thread
from threads import monitor_thread
from threads import EVT_PROCESS_DONE_EVENT

# Reminder: numpy array dimensions are typically indexed Y,X,Z
#           To add further confusion screen, the top left corner is the
#           origin (0,0) while the program "ncview" uses the bottom left
#           corner as the origin.
#
# TODO: make panel have horizontal scroll bar when number of operators
#       exceed panel space

# sets up panels graphics, provides operators with source data and 
# formats images and navigation to dispay panel
# initiates operator processing thread
class op_panel( op, wx.Panel ):

    # initialize but no graphics 
    def __init__( self, name ):
       
        op.__init__( self, name )
        self.band_tags = None   # band names

        self.nav_data = None    # 2 band image (lat,long); can be any measure
        self.nav_tags = None    # list unit label for nav measure

        self.angles = None      # sat and sun angles
        self.overlay = None     # 2-d image uint8 layer 
                                # political, cil, etc. 
                                # keep raw image for hdf writing

        self.hist = None        # histogram array of sink data
 
        self.display_overlay_image = None

    ####################################################################
    # gui section
    ####################################################################

    def get_source_op( self, offset ):
        
        index = self.benchtop.op.index( self )    # discover our index 
        if  offset > index or offset <= 0:        # check for invalid offset
            eprint( 'op_panel: get_source: invalid offset value' )
            eprint( 'op_panel: get_source: no source operator?' )
            return None
        
        neighbor = index-offset                   # get neighbor index
        return self.benchtop.op[neighbor]
    
    # get the sink (output) data from an operator neighbor
    def get_source( self, offset ):

        src_op = self.get_source_op( offset )
        if src_op == None:
            return None
        
        #self.attr = src_op.attr   # get sat info 
        #self.source_name = src_op.source_name
        return src_op.sink        # return neighbor sink

    # get the areal and band/nav tags from a neighbor
    # operator and set as ours
    def set_areal_tags( self, offset ):
        
        index = self.benchtop.op.index( self )    # discover our index 
        if offset > index or offset <= 0:         # check for invalid offset
            eprint( 'op_panel:set_areal_tags: invalid offset value' ) 
            eprint( 'op_panel:set_areal_tags: no source operator?' )
            return

        neighbor = index-offset                   # get neighbor index 

        # inherit source info
        source_op = self.benchtop.op[neighbor]    # get neighbor operator 

        self.areal_index = source_op.areal_index  # follow display format
        self.band_tags = source_op.band_tags      # from source. overide values
        self.nav_data = source_op.nav_data        # in sub operator, if needed.
        self.nav_tags = source_op.nav_tags        # eg. ops that change shape 
                                                  #     or navigation
        self.angles = source_op.angles

        self.overlay = source_op.overlay
        self.overlay_image = source_op.overlay_image

    # initialize graphics 
    def init_panel( self, benchtop ):
        
        wx.Panel.__init__( self, benchtop.op_note )

        self.benchtop = benchtop          #shorthand
       
        self.messages = benchtop.messages
        self.report = benchtop.report

        self.setup_items()                # base gui
        
        self.display_image = None
        self.overlay_image = None
        self.thumb_image = None

        self.lut = None 
        benchtop.pan_tools.settings.Enable( True )

        # areal_index keeps track of origin and scale for op_panel.
        # create a new areal_index in subclass by setting
        # areal_index = None in subclass; image will be centered
        # and a new index assigned. if changing shape don't forget 
        # to adjust nav_data, etc.
        # self.areal_index = None
        #
        # UPDATE: setting areal_index is now done in the apply_work 
        #       routine *_src (source) programs
        #
        self.Bind( EVT_PROCESS_DONE_EVENT, self.on_process_done )

    def on_process_done( self, event ):
        
        self.app_thread.join()            # wait for app thread to finish
  
        self.report.SetLabel( ' ' )
        self.report.SetLabel( self.name + ' processing done.' )

        # report process duration
        process_time = '%.3f' % event.duration
        self.messages.append('\tprocessing time:\t' +
                              process_time + ' s'  + '\n' )

        if not isinstance( self.sink, np.ndarray ):

            self.report.SetLabel( 'no output image' )
            self.messages.append( '\tno output image\n' )
            self.benchtop.clear()
            self.finalize()
            return

        self.report.SetLabel( 'rendering image...' )
        start = time.time()

        self.show_image() 

        duration = time.time()-start      # measure display rendering time
        self.report.SetLabel( 'rendering done.' )

        # show tag label
        if self.band_tags != None:

            band = self.s_band.GetValue()
            self.l_tag.SetLabel( self.band_tags[band] )

        process_time = '%.3f' % duration       
        self.messages.append('\trendering time:\t' +  
                              process_time + ' s'  + '\n' )
        self.finalize()
        self.report_image( self.sink )
        
    def setup_items( self ):
       
        # this panel consists of three sub-panels:
        # two panels (command, and color band merge) are managed by this
        # class while the third panel is managed by the sub class

        # start with top vertical sizer
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.AddSpacer( 4 )

        # top panel has 2 horizontal panels: command buttons and sub-class
        # client panels
        
        # create command panel ( start, cascade, cancel, options )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.AddSpacer( 3 )

        panel = self.command_panel()
        h_sizer.Add( panel )
        h_sizer.AddSpacer( 4 )

        # client panel; gets filled in by client operators
        self.p_client = wx.Panel( self, wx.ID_ANY, style=wx.SUNKEN_BORDER )
        h_sizer.Add( self.p_client, 1 ) #, wx.EXPAND|wx.ALL, 1 )
        
        v_sizer.Add( h_sizer, 0, wx.EXPAND|wx.ALL, 1 ) # top sizer is complete
        v_sizer.AddSpacer( 4 )

        # bottom panel; holds spinner band view, merger, clear image items
        panel = self.bottom_panel()
        v_sizer.Add( panel )
        v_sizer.AddSpacer( 3 )
        
        self.SetSizer( v_sizer )
    
        # disable band components
        self.enable_color( False )
        self.s_band.Enable( False )
        self.l_tag.Enable( False )
        self.c_merge.Enable( False )
        self.b_clear_display.Enable( False )
        
    def bottom_panel( self ):

        p_bottom = wx.Panel( self, wx.ID_ANY ) #, style=wx.SUNKEN_BORDER )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        
        # spinner; band to view
        self.s_band = wx.SpinCtrl(p_bottom, -1, "",
                                  (1,4), #(100,20), 
                                  style=wx.SP_WRAP|wx.SP_ARROW_KEYS )
        self.s_band.SetRange( 0, 0 )
        self.s_band.SetValue( 0 )
        self.s_band.SetToolTip( 'select an image band to view' )
        self.s_band.Bind( wx.EVT_SPINCTRL, self.on_spin )
        h_sizer.AddSpacer( 4 )
        h_sizer.Add( self.s_band )
        h_sizer.AddSpacer( 10 )
        
	# tag label
        self.l_tag = wx.StaticText( p_bottom, -1,
                                    '                      ' )
                                  #  (105,10) ) #,(155,20) )
        self.l_tag.SetToolTip( 'band tag' )
        h_sizer.Add( self.l_tag, 1, wx.ALIGN_CENTER_VERTICAL, 1  )
        h_sizer.AddSpacer( 40 )
        
        # imbed a new horizontal sizer for color management
        panel = self.color_panel( p_bottom )
        h_sizer.Add( panel, 0, wx.ALIGN_CENTER_VERTICAL, 1 )
        h_sizer.AddSpacer( 10 )

        # clear display button
        self.b_clear_display = wx.Button( p_bottom, -1, 'clear display' )
        self.b_clear_display.Bind( wx.EVT_LEFT_UP, self.on_clear_display )     
        self.b_clear_display.SetToolTip( 'clear the display' )
        h_sizer.Add( self.b_clear_display )
      
        p_bottom.SetSizer( h_sizer )
        return p_bottom

    def color_panel( self, p_bottom ):

        p_color = wx.Panel( p_bottom, wx.ID_ANY )#, style=wx.SUNKEN_BORDER )
  
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        # merge checkbox
        h_sizer.AddSpacer( 10 )
        self.c_merge = wx.CheckBox( p_color, wx.ID_ANY, 'merge' )#, (200,18) )
        self.c_merge.Bind( wx.EVT_CHECKBOX, self.on_merge )             
        self.c_merge.SetToolTip( 'view image as color band merge' )
        h_sizer.Add( self.c_merge, 0, wx.ALIGN_CENTER_VERTICAL, 1 )
        
        # red
        h_sizer.AddSpacer( 10 )
        self.p_red = wx.StaticText( p_color, wx.ID_ANY, 'RED = ' )
        h_sizer.Add( self.p_red, 0, wx.ALIGN_CENTER_VERTICAL, 1 )
        
        self.t_red = wx.TextCtrl( p_color, -1, '0',
                                  size=(50,20), style=wx.ALIGN_RIGHT )
        self.t_red.SetToolTip( 'enter band number for red' )
        h_sizer.Add( self.t_red, 0, wx.ALIGN_CENTER_VERTICAL, 1 )

        # green
        h_sizer.AddSpacer( 10 )
        self.p_green = wx.StaticText( p_color, wx.ID_ANY, 'GREEN = ' )
        h_sizer.Add( self.p_green, 0, wx.ALIGN_CENTER_VERTICAL, 1 )

        self.t_green = wx.TextCtrl( p_color, wx.ID_ANY, '1',
                                    size=(50,20),style=wx.ALIGN_RIGHT )
        self.t_green.SetToolTip( 'enter band number for green' )
        h_sizer.Add( self.t_green, 0, wx.ALIGN_CENTER_VERTICAL, 1 )

        # blue
        h_sizer.AddSpacer( 10 )
        self.p_blue = wx.StaticText( p_color, wx.ID_ANY, 'BLUE = ' )
        h_sizer.Add( self.p_blue, 0, wx.ALIGN_CENTER_VERTICAL, 1 )
        
        self.t_blue = wx.TextCtrl( p_color, wx.ID_ANY, '2',
                                   size=(50,20), style=wx.ALIGN_RIGHT )
        self.t_blue.SetToolTip( 'enter band number for blue' )
        h_sizer.Add( self.t_blue, 0, wx.ALIGN_CENTER_VERTICAL, 1 )
        
        p_color.SetSizer( h_sizer )
        return p_color

    def command_panel( self ):

        p_command = wx.Panel( self, -1)
        v_sizer = wx.BoxSizer( wx.VERTICAL )

        # command buttons
        self.b_apply = wx.Button( p_command, -1, 'apply' )
        self.b_apply.Bind( wx.EVT_LEFT_UP, self.on_apply )             
        self.b_apply.SetToolTip( 'run this operator' )
        v_sizer.Add( self.b_apply )
        v_sizer.AddSpacer( 4 )

        self.b_cascade = wx.Button( p_command, -1, 'cascade' )
        self.b_cascade.Bind( wx.EVT_LEFT_UP, self.on_cascade )             
        self.b_cascade.SetToolTip( 'run this and forward operators' )
        self.b_cascade.Enable( True )
        v_sizer.Add( self.b_cascade )
        v_sizer.AddSpacer( 4 )

        self.b_cancel = wx.Button( p_command, -1, 'cancel' )
        self.b_cancel.Bind( wx.EVT_LEFT_UP, self.on_cancel )             
        self.b_cancel.SetToolTip( 'cancel processing' )
        self.b_cancel.Enable( False )
        v_sizer.Add( self.b_cancel )
        v_sizer.AddSpacer( 4 )

        self.b_options = wx.Button( p_command, -1, 'options' )
        self.b_options.Bind( wx.EVT_LEFT_UP, self.on_options )             
        self.b_options.SetToolTip( 'operator option menu' )
        self.b_options.Enable( True )
        v_sizer.Add( self.b_options )
        v_sizer.AddSpacer( 5 ) # push to bottom of frame

        p_command.SetSizer( v_sizer )
        return p_command

    def on_options( self, event ):   # pop up options menu
        
        menu = wx.Menu()

        item = menu.Append( -1, 'read parameters...' )
        self.Bind( wx.EVT_MENU, self.on_read_params, item )
        menu.AppendSeparator()

        item = menu.Append( -1, 'write parameters as...')
        self.Bind( wx.EVT_MENU, self.on_write_params_as, item )
        menu.AppendSeparator()

        item = menu.Append( -1, 'save image as...' )
        self.Bind( wx.EVT_MENU, self.on_save_image_as, item )
        menu.AppendSeparator()

        # grey out menu item if no sink buffer
        if not isinstance( self.sink, np.ndarray ):
            item.Enable( False )
            
        item = menu.Append( -1, 'save numpy buffer as...' )
        self.Bind( wx.EVT_MENU, self.on_save_numpy_buffer_as, item )
        menu.AppendSeparator()

        if not isinstance( self.sink, np.ndarray ):
            item.Enable( False )

        self.PopupMenu( menu, (87,0) )
        menu.Destroy() 

    def on_read_params( self, event ):
        
        dlg = wx.FileDialog( self, "Choose a file to read", 
                            os.getcwd(), "", "*", wx.FD_OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.read_params_from_file( path )   
            self.write_params_to_panel()  # update params to gui

        dlg.Destroy()

    def on_write_params_as( self, event ):
        
        dlg = wx.FileDialog( self, "Choose a file to write", 
                             os.getcwd(), "", "*", 
                             wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.read_params_from_panel()        # update params from gui
            self.write_params_to_file( path )

        dlg.Destroy()

    # override in subclass
    def read_params_from_panel( self ):
        eprint( 'op_panel: read_params_from_panel: do not call directly' )

    # override in subclass
    def write_params_to_panel( self ):
        eprint( 'op_panel: write_params_to_panel: do not call directly' )

    def save_image( self, path ):
        
        wximage =  self.display_image.ConvertToImage()
        pil = Image.new('RGB', (wximage.GetWidth(), 
                                wximage.GetHeight()) )
        pil.frombytes( bytes( wximage.GetData()) )
        pil.save( path )
        
    def on_save_image_as( self, event ):        
        dlg = wx.FileDialog( self, "Save image as...", 
                             os.getcwd(), "", "*", 
                             wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT )

        if dlg.ShowModal() == wx.ID_OK:
            self.save_image( dlg.GetPath() )            
        dlg.Destroy()

    def on_save_numpy_buffer_as( self, event ):        
        dlg = wx.FileDialog( self, "Save numpy buffer as...", 
                             os.getcwd(), "", "*", 
                             wx.FD_SAVE|wx.FD_OVERWRITE_PROMPT )

        if dlg.ShowModal() == wx.ID_OK:
            fpath = dlg.GetPath()
            np.save( fpath, self.sink, allow_pickle=True )
            #self.sink.dump( dlg.GetPath() ) # doesn't work
            
        dlg.Destroy()

    def on_apply( self, event ):   # respond to apply click

        # get parameter values from panel
        if not self.read_params_from_panel():
            return            # parameters not valid
 
        # report to message box
        self.messages.append ( '\n\tid:\t\t\t\t' + self.op_id + '\n' )

        self.b_apply.Enable( False )
        self.b_cascade.Enable( False )
        self.b_cancel.Enable( True )

        self.c_merge.Enable( False )
        self.b_options.Enable( False )

        '''
        # non-thread version
        self.apply_work()

        if ( self.sink.ndim == 2 ) :
            self.show_band( self.sink )
        else :
            self.show_band( self.sink[0] )

        self.finalize()
        '''

        text =  'processing ' + self.name
        self.report.SetLabel( text )

        # spawn processing thread
        self.app_cancelled = False     
        self.app_thread = apply_thread( self ) 
        self.app_thread.start()

        # spawn another thread to keep track of processing thread
        self.mon_thread = monitor_thread( self )
        self.mon_thread.start()

    def finalize( self ):               # clean up after a run
        
        self.b_apply.Enable( True )     # restore buttons
        self.b_cascade.Enable( True )
        self.b_cancel.Enable( False )
        self.b_options.Enable( True )
        self.b_clear_display.Enable( True )
        
    # set up processing; called from app thread
    def apply_work( self ):           
        
        # get input image from a neighbor operator
        self.source = self.get_source( 1 )

        #if type( self.source ) is not np.ndarray:
        if not isinstance( self.source, np.ndarray ):
            eprint( 'op_panel: apply_work: ' + \
                    'neighbor sink (output) image not set' )
            return

        self.set_areal_tags( 1 )        # inherit nav and band tags
        self.run()                      # run the operator

        # check if valid run output
        #if type( self.sink ) is not np.ndarray:
        if not isinstance( self.sink, np.ndarray ):

            eprint( 'op_panel: run output buffer not valid...returning' )
            return

    def on_cascade( self, event ):      # respond to cascade click
        
        index = self.benchtop.op.index( self )    # discover our index 
        size = len( self.benchtop.op )            # how many ops are there?
        
        for i in range( index, size ):
            self.benchtop.op[i].on_apply( None )
            
            # wait for thread to clean up
            while self.benchtop.op[i].app_thread.is_alive():
                time.sleep( 0.2 )

    def on_cancel( self, event ):       # kill processing

        # set internal flag to cancel
        self.app_cancelled = True       # app has to check this
                                        # for cancel to work
        self.messages.append( self.name + 
                              ' processing cancelled\n' )
        # wait for thread to clean up
        while self.app_thread.is_alive():
            time.sleep( 0.1)

    def check_bands( self ):
        
        nbands = self.sink.shape[2]
        
        # check if rgb bands ok
        red = int (self.t_red.GetValue().strip() )
        if red  >= nbands or red < 0:
            eprint( 'op_panel: check_bands: red buffer value is bad' )
            eprint( '           got:', red, ' setting to 0' )
            red = 0
            self.t_red.SetValue( '0' )

        green = int( self.t_green.GetValue().strip() )
        if green >= nbands or green < 0:
            eprint( 'op_panel: check_bands: green buffer value is bad' )
            eprint( '           got:', green, ' setting to 1' )
            green = 1
            self.t_green.SetValue( '1' )

        blue = int( self.t_blue.GetValue().strip() )
        if blue  >= nbands or blue < 0:
            eprint( 'op_panel: check_bands: blue buffer value is bad' )
            eprint( '           got:', blue, ' setting to 2' )
            blue = 2 
            self.t_blue.SetValue( '2' )    

        return red, green, blue
        
    # trigger merging of three bands for color display
    def on_merge( self, event ):        # respond to merge checkbox

        if not self.c_merge.GetValue():
            
            #self.enable_color( False )
            self.s_band.Enable( True )
            self.l_tag.Enable( True )
            self.benchtop.pan_tools.settings.Enable( True )
            self.buf_lut = [ self.s_band.GetValue() ]
            self.render( self.buf_lut )
            return
        
        nbands = self.sink.shape[2]
 
        if nbands < 3:
            eprint( 'op_panel: not enough buffers to make color image' )
            eprint( '          got:', nbands, ' ...returning' )
            return

        r,g,b = self.check_bands()
        
        self.enable_color( True )
        self.s_band.Enable( False )
        self.l_tag.Enable( False )
        
        self.benchtop.pan_tools.settings.Enable( False )
        
        self.buf_lut = [ r, g, b ]
        self.render( self.buf_lut )
        
    ''' 
    def on_merge_apply( self, event ):  # respond to merge checkbox
        self.render( self.buf_lut )
    '''
    
    # respond to clear display checkbox
    def on_clear_display( self, event ):
        
        self.benchtop.clear()
        self.enable_color( False )
        self.c_merge.SetValue( False )
        self.c_merge.Enable( False )
        self.s_band.Enable( False )
        self.l_tag.SetLabel( '' )

        self.sink = None

        self.b_clear_display.Enable( False )

    def enable_color( self, toggle ):

        self.p_red.Enable( toggle )
        self.t_red.Enable( toggle )
        
        self.p_green.Enable( toggle )
        self.t_green.Enable( toggle )
        
        self.p_blue.Enable( toggle )
        self.t_blue.Enable( toggle )

    def on_spin( self, event ):         # band spinner

        index = self.s_band.GetValue()

        if self.band_tags != None:
             self.l_tag.SetLabel( self.band_tags[index] )

        self.buf_lut = [index]
        self.render( self.buf_lut )\

        event.Skip()

    # this gets called when processing is done
    # or when redisplay is requested
    def show_image( self ):

        #if type( self.sink ) is not np.ndarray:
        if not isinstance( self.sink, np.ndarray ):
             return

        # easiest first
        
        #if type(self.overlay_image) is not np.ndarray:
        if not isinstance( self.overlay_image, np.ndarray ):
            self.display_overlay_image = None
        else:
            self.display_overlay_image = self.render_overlay_bmp(self.overlay_image)

        nbands = self.sink.shape[2]           # set spinner maximum
        current_band = self.s_band.GetValue() # get band value from spinner

        # check if spinner band is out of bounds (in case of new image)
        if current_band > (nbands-1):
            self.s_band.SetValue( 0 )

            if self.band_tags != None:
                self.l_tag.SetLabel( self.band_tags[0] )

        self.s_band.SetRange( 0, nbands-1 )
         
        if nbands > 2 :        # enable merge if at least 3 bands
              
            # enable checkbox
            self.c_merge.Enable( True )      # ungrey check box

            # check if rgb bands ok
            r,g,b = self.check_bands()            
            self.enable_color( True )
 
        else:
            self.c_merge.Enable( False )
            self.enable_color( False )
            
            self.s_band.Enable( True )
            self.l_tag.Enable( True )
       
	# display image according to merge check box
        if self.c_merge.GetValue() and nbands > 2:
            self.s_band.Enable( False )
            self.l_tag.Enable( False )
            self.buf_lut = [ r, g, b ] # from rgb assignment in panel
            
        else:
            self.c_merge.SetValue( False )
            self.buf_lut = [ current_band ]
            self.s_band.Enable( True )
            self.l_tag.Enable( True )
  
        self.render( self.buf_lut )
    
    # filter out Nans in input data and then calculate display image histogram 
    def get_histogram( self, buf ):       

        height,width = buf.shape
        buf = np.reshape( buf, height*width )
        #buf.shape = ( height*width )
        
        n = buf[ ~np.isnan( buf ) ] # remove nan entries
 
        if buf.dtype != np.uint8:
            
            # scale values to 0-255
            try:
                n = (255*(n - np.min(n)) / np.ptp(n)).astype(np.uint8)
                
            except:
                eprint( 'op_panel: get_histogram:' )
                eprint( '          cannot calculate histogram...returning' )
                return None

        hist,edges = np.histogram( n, 256, (0.0,255.0) )
        hist.shape = 1, len( hist ) # reshape to 1-band, 256

        return hist
    
    # convert single-banded image to byte datatype for display
    def recast_band( self, image ):

        # scale values to 0-255
        '''
        simage = (255*(image - np.nanmin(image)) / np.ptp(image)).astype(np.uint8)
        return simage
        '''
        nmin = np.nanmin( image )       # get values to scale by
        nmax = np.nanmax( image )       # ignoring nan

        if nmax == nmin :               # check for constant values
            scale = 0.0 	        # make image a surface plane
            c = 0.0
        else:
            # TODO: handle min=-inf,max=inf
            if np.isinf( nmin ):
                eprint( 'op_panel: recast_band: min is infinty...returning'  )
                return

            if np.isinf( nmax ):
                eprint( 'op_panel: recast_band: max is infinty...returning'  )

            scale = 255.0/(nmax-nmin)    # plain stretch to 8-bit range
            c = -scale*nmin

        b_image = (image*scale)
        b_image = (b_image + c).astype( np.uint8 )    
        return b_image
        
    # end recast_band
    
    # paint single band for grey level or three bands for a color display
    def render( self, indexes ):

        # indexes is buffer lookup table for color mapping;
        # grey levels have a len(indexes) of 1
        # color has len(indexes) of 3
        height, width, nbands = self.sink.shape
        size = len( indexes )
        if size not in [1,3]:
            eprint( 'op_panel: render: size of indexes array must be 1 or 3' )
            eprint( '                  got:', size, ' ,,,returning' )
            return

        # setup output
        height, width, nbands = self.sink.shape
        image = np.zeros( (height,width,size),  dtype=np.uint8 )
        self.hist = np.empty( (size,256), dtype=np.int32 )

        j = 0
        for i in indexes:

            if np.isnan( self.sink[:,:,i] ).all() : 
                eprint( 'op_panel: show_merge: data buffer=', i, '  is all NaN')
                eprint( '          replaced image buffer with zeros' )
                hist = np.zeros( (1,256), dtype=np.int32 )
                hist[0,0] = height*width     # make our own histogram
                                             # since we know the values
                self.hist[j,:] = hist

            # check for boolean type
            elif self.sink.dtype == np.bool:
                image[:,:,j] = self.sink[:,:,i]*255 # make True == 255
                self.hist[j,:] = self.get_histogram( image[:,:,j] )

            # check if data type is byte for direct display
            elif self.sink.dtype == np.uint8: 
                image[:,:,j] = self.sink[:,:,i]
                self.hist[j,:] = self.get_histogram( self.sink[:,:,i] )

            # recast dtype to uint8 for display
            else:
                image[:,:,j] = self.recast_band( self.sink[:,:,i] )
                self.hist[j,:] = self.get_histogram( self.sink[:,:,i] )

            # TODO:report max,min values in the navigation benchtop panel
            # report max and min values
            dmin = np.nanmin( self.sink[:,:,i] )
            dmax = np.nanmax( self.sink[:,:,i] )

            if size == 1:
                self.benchtop.pan_tools.nav.l_grey_min.SetLabel( '%.3f'%float(dmin) )
 
                self.benchtop.pan_tools.nav.l_grey_max.SetLabel( '%.3f'%float(dmax) )

                self.benchtop.pan_tools.nav.l_red_min.SetLabel( 'n/a' )
                self.benchtop.pan_tools.nav.l_red_max.SetLabel( 'n/a' )
  
                self.benchtop.pan_tools.nav.l_green_min.SetLabel( 'n/a' )
                self.benchtop.pan_tools.nav.l_green_max.SetLabel( 'n/a' )

                self.benchtop.pan_tools.nav.l_blue_min.SetLabel( 'n/a' )
                self.benchtop.pan_tools.nav.l_blue_max.SetLabel( 'n/a' ) 
   
            else:
                self.benchtop.pan_tools.nav.l_grey_min.SetLabel( 'n/a' )
                self.benchtop.pan_tools.nav.l_grey_max.SetLabel( 'n/a' )

                if i == 0:
                    self.benchtop.pan_tools.nav.l_red_min.SetLabel( '%.3f'%float(dmin) )
                    self.benchtop.pan_tools.nav.l_red_max.SetLabel( '%.3f'%float(dmax) )
                    
                elif i == 1:
                    self.benchtop.pan_tools.nav.l_green_min.SetLabel( '%.3f'%float(dmin) )
                    self.benchtop.pan_tools.nav.l_green_max.SetLabel( '%.3f'%float(dmax) )
                    
                elif i == 2:
                    self.benchtop.pan_tools.nav.l_blue_min.SetLabel( '%.3f'%float(dmin) )
                    self.benchtop.pan_tools.nav.l_blue_max.SetLabel( '%.3f'%float(dmax) )
                    
            '''
            message = '\tbuffer min = ' + '%.3f'%dmin + ' max = ' + '%.3f'%dmax + '\n'
            self.messages.append( message )
            eprint( message )
            '''            
            j += 1
            
        # make it a wx bmp
        self.display_image = self.render_bmp( image )
        self.set_thumb_image()   # construct the thumb (pan) image

        # let benchtop distribute images;  start new registry index        
        self.benchtop.set_images( self, self.areal_index )  
 
    # create a thumb panner image
    def set_thumb_image( self ):
        
        if self.display_image == None:
            return

        # get thumb (panner) panel dimensions
        p_width, p_height = self.benchtop.pan.get_inner_size()
        max_size = float( p_width )   # make it float for factor 

        # calculate scale for thumb image
        width,height = self.display_image.GetSize()

        if  width >= height:
            factor = max_size/width;
        else:
            factor = max_size/height;

        # calculate size of thumb image
        height = int(height*factor)
        width = int(width*factor)
        
        image = self.display_image.ConvertToImage()
        image = image.Scale(width, height)
        self.thumb_image = wx.Bitmap( image )

    # render into bmp format
    def render_bmp( self, image ):
        
        height,width,nbands = image.shape
        #bmp = wx.EmptyBitmap( width, height, 24 )
        bmp = wx.Bitmap( width, height, 24 )

        if nbands == 1:
            #if type( self.lut ) is not np.ndarray:
            if not isinstance( self.lut, np.ndarray ):
 
                rgb = self.enlarge( image, 3, 1 )
            else:
                # run image through lut 
                rgb = self.lut[ image ]  # just indexing
 
            bmp.CopyFromBuffer( rgb.tostring() )
        else:
            bmp.CopyFromBuffer( image.tostring() ) # true color

        return bmp

    # render overlay image into bmp format
    def render_overlay_bmp( self, image ):
        
        height,width,nbands = image.shape
        #bmp = wx.EmptyBitmap( width, height, 32 )
        bmp = wx.Bitmap( width, height, 32 )

        if nbands != 4:
            eprint( 'op_panel:render_overlay_bmp: image must be RGBA' )
            return

        bmp.CopyFromBuffer( image.tostring(),format=wx.BitmapBufferFormat_RGBA )
        return bmp

    def enlarge( self, a, x=2, y=None ):     # replicate bands
        if y == None:
            y=x                              # do same for y dimension

        return a.repeat(y, axis=0).repeat(x, axis=1)

    def report_image( self, image ):
        
        height,width,nbands = image.shape
        self.messages.append( '\tnum bands:\t\t' + str(nbands) + '\n' )
        self.messages.append( '\tdimensions:\t' )
        self.messages.append( str(width) + ' x ' + str(height) + ' pixels\n' )
        self.messages.append( '\tdata type:\t\t' + str(image.dtype) + '\n' )


