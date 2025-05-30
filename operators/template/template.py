#! /usr/bin/env python3

'''
@file blur.py
@author Scott L. Williams.
@package POLI
@brief rudimentary template for POLI
@LICENSE

# template.py Copyright (C) 2025 Scott L. Williams
# 
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed infilename the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
# 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

@sections DESCRIPTION
a simple framework for POLI operators
'''

# embed copyright in binary
template_copyright = 'template.py Copyright (c) 2025 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

#  template code for poli operators
import os
import wx
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint

# determine if graphics can be enabled
try:
    import wx
    from op_panel import op_panel
    from filedrop import FileDrop      # drag and drop a file
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
# if not then assume non-graphics implementaion
except:
    from op import op
    operator = op
    eprint( 'template: using non-graphics mode.' )

def get_name():                    
    return 'template'

# return an instance of 'template' class 
def instantiate():	
    return template( get_name() )

class template_parameters( pio ):
    
    def __init__( self ):

        # example variables
        self.checkboxa = False
        self.checkboxb = False
        self.checkboxc = False
 
        self.filepath = ''
        self.radio_selection = 1

        self.value1 = 100.0
        self.value2 = 200.0
        self.value3 = 300.0

    def print_params( self ):
        
        eprint( '\nparameters for template:' )
        eprint( '      checkboxa =', self.checkboxa )
        eprint( '      checkboxb =', self.checkboxb )
        eprint( '      checkboxc =', self.checkboxc )
        eprint( '      filepath  =', self.filepath )
        eprint( 'radio selection =', self.radio_selection )
        eprint( '    first value =',  self.value1 )
        eprint( '   second value =', self.value2 )
        eprint( '    third value =',  self.value3 )
        
# ---------------------------------------------------------------------------

class template( op_panel ):
    
    def __init__( self, name ): # initialize op_panel but no graphics

        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = template_parameters()

    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    # override superclass run
    def run( self ):

        # put operator functions here
        self.p.print_params()
        self.print_versions()

    ####################################################################
    # gui section
    ####################################################################

    def set_filepath( self, obj ):
        
        if isinstance( obj, str ):             # we've been invoked by
            obj.strip()                        # image_tree or file drop
            self.t_filepath.SetValue( obj )

        '''
        if self.p.apply_on_file_drop:
            self.on_apply( None )
        '''

    # override since we are a template; won't need to do this
    # for regular operators
    def apply_work( self ):
        
        self.run()          # run the operator

    def read_params_from_panel( self ):     # scan panel parameters
        
        self.p.checkboxa = self.c_checkboxa.IsChecked()
        self.p.checkboxb = self.c_checkboxb.IsChecked()
        self.p.checkboxc = self.c_checkboxc.IsChecked()
 
        self.p.filepath = self.t_filepath.GetValue()
        
        if self.r_radiobutton1.GetValue():
            self.p.radio_selection = 1
            
        elif self.r_radiobutton2.GetValue():
            self.p.radio_selection = 2
            
        elif self.r_radiobutton3.GetValue():
            self.p.radio_selection = 3

        else:
            eprint( 'template: read_params_from_panel: unknown radio button' )

        self.p.value1 = float( self.t_value1.GetValue() )
        self.p.value2 = float( self.t_value2.GetValue() )
        self.p.value3 = float( self.t_value3.GetValue() )

        return True 
 
    def write_params_to_panel( self ):      # write paramers to panel
        
        self.c_checkboxa.SetValue( self.p.checkboxa )
        self.c_checkboxb.SetValue( self.p.checkboxb )
        self.c_checkboxc.SetValue( self.p.checkboxc )
       
        self.t_filepath.SetValue( self.p.filepath  )

        if  self.p.radio_selection == 1:
            self.r_radiobutton1.SetValue( True )
            
        if  self.p.radio_selection == 2:
            self.r_radiobutton2.SetValue( True )
            
        if  self.p.radio_selection == 3:
            self.r_radiobutton3.SetValue( True )

        self.t_value1.SetValue( str(self.p.value1) )
        self.t_value2.SetValue( str(self.p.value2) )
        self.t_value3.SetValue( str(self.p.value3) )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        operator.init_panel( self, benchtop ) # start with basics
        
        # panel sizers (vertical and horizontal)
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        
        # make radio_panel and add to horizontal sizer
        panel = self.radiobuttons_panel()
        h_sizer.Add( panel )
        
        # put some space after radio_panel
        h_sizer.Add( 10,1 )
        
        # make checkbox panel and add to horizontal sizer
        panel = self.checkboxes_panel()
        h_sizer.Add( panel )

        # put some space after radio_panel
        h_sizer.Add( 10,1 )
        
        # make buttons panel and add to horizontal sizer
        panel = self.buttons_panel()
        h_sizer.Add( panel )

        # values subpanel
        panel = self.values_panel()

        h_sizer.Add( panel )
        
        # add h_sizer to v_sizer
        v_sizer.Add( h_sizer )

        # add some space after h_sizer
        v_sizer.Add( 1, 5 )
        
        # make filepath text control panel
        panel = self.filepath_panel()

        # add to v_sizer
        v_sizer.Add( panel, 1, wx.EXPAND )
 
        # add v_sizer to op_panel
        self.p_client.SetSizer( v_sizer )

        # populate panels with values from self.p
        self.write_params_to_panel()

    # make panel for filepath
    def values_panel( self ):
        
        p_values = wx.Panel( self.p_client, -1 )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1,5 )

        # first value input text control
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( 4, 1 ) # spacer from left

        # first value input text control
        prompt = wx.StaticText( p_values, -1, 'value 1:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 5, 1 )
        
        self.t_value1 = wx.TextCtrl( p_values, -1, '', style=wx.ALIGN_RIGHT,
                                     size=(60,20) )
        self.t_value1.SetToolTip( 'enter first value' )
        
        h_sizer.Add( self.t_value1 )
        v_sizer.Add( h_sizer )
        
        # second value input text control
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( 4, 1 ) # spacer from left

        prompt = wx.StaticText( p_values, -1, 'value 2:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 5, 1 )
        
        self.t_value2 = wx.TextCtrl( p_values, -1, '', style=wx.ALIGN_RIGHT,
                                     size=(60,20) )
        self.t_value2.SetToolTip( 'enter second value' )
        h_sizer.Add( self.t_value2 )
        v_sizer.Add( h_sizer )
        
        # third value input text control
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( 4, 1 ) # spacer from left

        prompt = wx.StaticText( p_values, -1, 'value 3:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 5, 1 )
        
        self.t_value3 = wx.TextCtrl( p_values, -1, '', style=wx.ALIGN_RIGHT,
                                     size=(60,20) )
        self.t_value2.SetToolTip( 'enter third value' )
        h_sizer.Add( self.t_value3 )
        v_sizer.Add( h_sizer )
        
        p_values.SetSizer( v_sizer )
        return p_values
 
    # make radio buttons subpanel
    def radiobuttons_panel( self ):
        
        # make panel
        p_radiobuttons = wx.Panel( self.p_client, -1 )

        # make GridBag sizer
        g_sizer = wx.GridSizer( 3, 1, 1, 1 )

        # mark the beginning of the group with wx.RB_GROUP
        self.r_radiobutton1 = wx.RadioButton( p_radiobuttons, -1, 'radio1', 
                                            style = wx.RB_GROUP )
        self.r_radiobutton1.Bind( wx.EVT_RADIOBUTTON, self.on_radiobutton1 )
        g_sizer.Add( self.r_radiobutton1 )
        
        self.r_radiobutton2 = wx.RadioButton( p_radiobuttons, -1, 'radio2' )
        self.r_radiobutton2.Bind( wx.EVT_RADIOBUTTON, self.on_radiobutton2 )
        g_sizer.Add( self.r_radiobutton2 )
        
        self.r_radiobutton3 = wx.RadioButton( p_radiobuttons, -1, 'radio3' )
        self.r_radiobutton3.Bind( wx.EVT_RADIOBUTTON, self.on_radiobutton3 )    
        g_sizer.Add( self.r_radiobutton3 )

        p_radiobuttons.SetSizer( g_sizer )
        return p_radiobuttons
  
    # make filepath panel
    def filepath_panel( self ):

        # make panel for filepath
        p_filepath = wx.Panel( self.p_client, -1 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( 4, 1 ) # spacer from left

        # file input text control
        prompt = wx.StaticText( p_filepath, -1, 'enter file:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 10, 1 )
        
        self.t_filepath = wx.TextCtrl( p_filepath, -1, '' )
        self.t_filepath.SetToolTip( 'enter filepath' )
        dt = FileDrop( self.t_filepath, self )
        self.t_filepath.SetDropTarget( dt )

        h_sizer.Add( self.t_filepath, 1, wx.EXPAND )
        
        b_browse = wx.Button( p_filepath, -1, 'browse' )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )

        h_sizer.Add( b_browse )
        
        p_filepath.SetSizer( h_sizer )
        return p_filepath
 
    # make buttons subpanel
    def buttons_panel( self ):

        # make panel with title 'buttons'
        p_buttons = wx.Panel( self.p_client, -1  )

        # make GridBag sizer
        g_sizer = wx.GridSizer( 3, 1, 1, 1 )

        b_button1 = wx.Button( p_buttons, -1, 'button1' )
        b_button1.Bind( wx.EVT_LEFT_UP, self.on_button1 )             
        b_button1.SetToolTip( 'press me button1' )
        g_sizer.Add( b_button1 )
        
        b_button2 = wx.Button( p_buttons, -1, 'button2' )
        b_button2.Bind( wx.EVT_LEFT_UP, self.on_button2 )             
        b_button2.SetToolTip( 'press me button2' )
        g_sizer.Add( b_button2 )
 
        b_button3 = wx.Button( p_buttons, -1, 'button3' )
        b_button3.Bind( wx.EVT_LEFT_UP, self.on_button3 )             
        b_button3.SetToolTip( 'press me button3' )
        g_sizer.Add( b_button3 )
 
        p_buttons.SetSizer( g_sizer )
        return p_buttons
      
    # make checkboxes panel
    def checkboxes_panel( self ):
        
        p_checkboxes = wx.Panel( self.p_client, -1 )
        
        # make GridBag sizer
        g_sizer = wx.GridSizer( 3, 1, 1, 1 )
        
        self.c_checkboxa = wx.CheckBox( p_checkboxes, -1, 'checkboxa' )
        self.c_checkboxa.Bind( wx.EVT_CHECKBOX, self.on_checka )        
        self.c_checkboxa.SetToolTip( 'check me 1' )
        g_sizer.Add( self.c_checkboxa )

        self.c_checkboxb = wx.CheckBox( p_checkboxes, -1, 'checkboxb' )
        self.c_checkboxb.Bind( wx.EVT_CHECKBOX, self.on_checkb )        
        self.c_checkboxb.SetToolTip( 'check me 2' )
        g_sizer.Add( self.c_checkboxb )
        
        self.c_checkboxc = wx.CheckBox( p_checkboxes, -1, 'checkboxc' )
        self.c_checkboxc.Bind( wx.EVT_CHECKBOX, self.on_checkc )        
        self.c_checkboxc.SetToolTip( 'check me 3' )
        g_sizer.Add( self.c_checkboxc )

        p_checkboxes.SetSizer( g_sizer )
        return p_checkboxes 

    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, "Choose an file to read", 
                             os.getcwd(), "", "*", wx.FD_OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath().strip()
            self.t_filepath.SetValue( path ) # update filepath to gui

        dlg.Destroy()

    def on_file_drop( self, event ):
        path = dlg.GetPath().strip()
        self.t_filepath.SetValue( path ) 
       
    def on_radiobutton1( self, event ):
        eprint( 'radiobutton1 =', self.r_radiobutton1.GetValue() )
        
    def on_radiobutton2( self, event ):
        eprint( 'radiobutton2 =', self.r_radiobutton2.GetValue() )

    def on_radiobutton3( self, event ):
        eprint( 'radiobutton3 =', self.r_radiobutton3.GetValue() ) 

    def on_checka( self, event ):
        eprint( 'checkboxa =', self.c_checkboxa.GetValue() ) 
    
    def on_checkb( self, event ):
        eprint( 'checkboxb =', self.c_checkboxb.GetValue() ) 
    
    def on_checkc( self, event ):
        eprint( 'checkboxc =', self.c_checkboxc.GetValue() ) 
    
    def on_button1( self, event ): # respond to button1 click
        eprint( 'pressed button1' )
        
    def on_button2( self, event ): # respond to button2 click
        eprint( 'pressed button2' )
        
    def on_button3( self, event ): # respond to button3 click
        eprint( 'pressed button3' )

    ####################################################################
    # command line user entry point 
    ####################################################################

    def usage( self ):
        
        eprint( 'usage: template.py' )
        eprint( '       -h, --help' )
        eprint( '       -a', '--acheck' )
        eprint( '       -b', '--bcheck' )
        eprint( '       -c', '--ccheck' )
        eprint( '       -r <1,2,3>, --radio=<1,2,3>' )
        eprint( '       -f filepath, --file=filepath' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )
        sys.exit( 2 )  
 
    def set_params( self,  argv ):
        
        params = None
        filepath = ''

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'habcr:f:p:d:',
                                        ['help','acheck','bcheck', 'ccheck',
                                         'params=','file='] )
                
        except getopt.GetoptError as e:
            eprint( 'template: ' + str(e) )
            self.usage()                          
                 
        for opt, arg in opts:
                
            if opt in ( '-h', '--help' ):      
                usage()                     

            if opt in ( '-a', '--acheck' ):      
                self.p.checkboxa = True

            if opt in ( '-b', '--bcheck' ):      
                self.p.checkboxb = True              

            if opt in ( '-c', '--ccheck' ):      
                self.p.checkboxc = True
                
            if opt in ( '-r', '--radio' ):
                self.radio_selection = int( arg )
                
            if opt in ('-p', '--params'):
                params = arg

            if opt in ('f', '--file' ):
                filepath = arg

        if params == None and filepath == '':
            eprint( 'must have paramfile or filepath' )
            self.usage()
                
        if params != None:
            
            ok = self.read_params_from_file( str(params) )
            if not ok:
                eprint( 'template: set_params: bad params file read...exiting' )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':

    oper = instantiate()      
    oper.set_params( sys.argv[1:] )

    import tempfile

    # numpy needs to 'seek' on the file to load
    # so read from stdin to temporary file
    
    temp_name = next( tempfile._get_candidate_names() ) + '.tmp'
    temp = open( temp_name, 'wb' )
    temp.write( sys.stdin.buffer.read() )
    temp.close()

    try:
        # load the numpy array data
        oper.source = np.load( temp_name, allow_pickle=True )
        oper.run()                  

        oper.sink.dump( sys.stdout.buffer )
        
    except Exception as e:
        eprint( str(e) )
            
    os.remove( temp_name )
