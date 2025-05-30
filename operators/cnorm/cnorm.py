#! /usr/bin/env python3

'''
@file cnorm.py
@author Scott L. Williams
@package POLI
@brief normalize all bands using predefined normalization coefficients.
@LICENSE
# 
#  cnorm.py Copyright (C) 2010-2025 Scott L. Williams.
# 
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
'''

# Normalize all bands according to predefined normalization coefficients
# ie. y = mx + c, from a file

cnorm_copyright = 'cnorm.py Copyright (c) 2010-2025 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint

# determine if graphics (wx.python) can be enabled
try:
    import wx
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
                                       
    class FileDrop( wx.FileDropTarget ):         # clean up text after drop
        
        def __init__( self, window, operator ):
            
            wx.FileDropTarget.__init__( self )
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
            except:
                eprint( 'cnorm: something went wrong with file drop...' )
                return False
        
# if not then assume non-graphics implementation
except:
    from op import op
    operator = op
    eprint( 'cnorm: using non-graphics mode.' )

def get_name(): 
    return 'cnorm'

# return an instance of 'cnorm' class 
def instantiate():	
    return cnorm( get_name() )

class cnorm_parameters( pio ):        # hold arguments values here
    
    def __init__( self ):
        
        self.ntype = None             # 0 for 0 to 1; -1 for -1 to 1
                                      # from input file
                                      
        self.clip = True              # clip to bounds
                                      # TODO: implement checkbox in GUI
        self.filepath = ''
        self.apply_on_file_drop = True

    def print_params( self ):
        
        eprint( '\nparameters for cnorm:' )
        eprint( '    clip               =', self.clip )
        eprint( '    filepath           =', self.filepath )
        eprint( '    apply on file drop =', self.apply_on_file_drop )
               
# ----------------------------------------------------------------------------

class cnorm( operator ):
    
    def __init__( self, name ):      # instantiate operator
        
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  

        self.cfile = None
        self.p = cnorm_parameters()

    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    # convert band range to floor to ceiling
    def scale_band( self, image, scale, offset, ntype ):

        norm = image*scale + offset

        # clip to bounds
        if self.p.clip:
            norm = np.clip( norm, ntype, 1 )
            
        return norm

    def run( self ):                 # override superclass 
      
        # read the number of bands and normalization type from file
        try:
            cfile = open( self.p.filepath, 'r' )
        except:
            eprint( 'cnorm: could not open file: ', self.p.filepath )
            return

        items = cfile.readline().split(',')
        numbands = int( items[0].strip() )
        ntype = int( items[1].strip() )
        if ntype not in [-1,0]:
            eprint( 'cnorm: ntype must be -1 or 0, got:', ntype, ' ...exiting' )
            sys.exit( 1 )
            
        self.p.print_params() # print out now that ntype is known
        self.print_versions()
 
        height,width,nbands = self.source.shape
        if numbands != nbands:
            eprint( 'cnorm: number of bands to not match' )
            return
        
        # create output buffer
        self.sink = np.empty( (height,width,nbands), dtype=np.float32 )

        # normalize each band according to coefficients
        for i in range( nbands ):
            
            line = cfile.readline()
            items = line.split(',')

            band = int( items[0].strip() )
            scale = float( items[1].strip() )
            offset = float( items[2].strip() )

            self.sink[:,:,band] = self.scale_band( self.source[:,:,band],
                                                   scale, offset, ntype )

    ####################################################################
    # gui section
    ####################################################################
    
    def set_filepath( self, obj ):
        
        if isinstance(obj, str):             # we've been invoked by
            obj.strip()                      # image_tree or file drop
            self.t_filepath.SetValue( obj )
            
        if self.p.apply_on_file_drop:
            self.on_apply( None )

    def read_params_from_panel( self ):      # scan panel parameters

        # set filename to use
        filepath = self.t_filepath.GetValue().strip()
        if not os.path.isfile( filepath ):
            eprint( 'cnorm: read_params_from_panel:' )
            eprint( '       file cannot be found:', filepath )
            eprint( '       ...returning' )
            return False
        
        self.p.filepath = filepath
        
        self.p.apply_on_file_drop = self.c_apply_on_file_drop.GetValue()
        self.p.clip = self.c_clip.GetValue()

        return True
    
    def write_params_to_panel( self ):       # write parameters to panel
        
        # write filepath
        self.t_filepath.SetValue( self.p.filepath )
        self.c_apply_on_file_drop.SetValue( self.p.apply_on_file_drop )
        self.c_clip.SetValue( self.p.clip )
       
    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1, 5 )
        prompt = wx.StaticText( self.p_client, -1,
                                '  read normalization coefficients file:' )
        v_sizer.Add( prompt )
        v_sizer.Add( (1,5) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        # filepath input text control
        prompt = wx.StaticText( self.p_client, -1, '  enter filepath:' )
        h_sizer.Add( prompt )
        
        self.t_filepath = wx.TextCtrl( self.p_client, -1, '', size=(500,30) )
        self.t_filepath.SetToolTip( 'enter filepath for norm coefficients' )
        dt = FileDrop( self.t_filepath, self )   
        self.t_filepath.SetDropTarget( dt )
        h_sizer.Add( self.t_filepath, wx.EXPAND )

        # browse directory button
        b_browse = wx.Button( self.p_client, -1, 'browse' )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        b_browse.SetToolTip( 'browse directory for data file' )
        h_sizer.Add( (1, 1),1 ) # '1' pushes button to right
        h_sizer.Add( b_browse )

        v_sizer.Add( h_sizer )
        v_sizer.Add( (1,10) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        # apply on file drop
        self.c_apply_on_file_drop = wx.CheckBox( self.p_client, -1,
                                                 'apply on file drop' )
        self.c_apply_on_file_drop.SetToolTip('run operator when file is dropped')
        self.c_apply_on_file_drop.Bind( wx.EVT_LEFT_UP, self.on_drop_click )
        h_sizer.Add( self.c_apply_on_file_drop )

        # clip
        self.c_clip = wx.CheckBox( self.p_client, -1, 'clip values' )
        self.c_clip.SetToolTip('clip values if greater than max')
        h_sizer.Add( self.c_clip )
        v_sizer.Add( h_sizer )

        self.p_client.SetSizer( v_sizer )
        
        self.write_params_to_panel()
        
    # respond to file browse click   
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, 'Choose a normalization coefficient file to read', 
                             os.getcwd(), "", "*", wx.FD_OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

    def on_drop_click( self, event ):

        if self.c_apply_on_file_drop.GetValue():
            self.p.apply_on_file_drop = False
        else:
            self.p.apply_on_file_drop = True

    def on_radio_click( self, event ):

        if self.r_ntype_half.GetValue():
            self.p.ntype = 0
        else:
            self.p.ntype = -1
 
    ############################################################
    # command line options for batch implementation
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: cnorm.py' )
        eprint( '    -h, --help' )
        eprint( '    -c, --clip' )
        eprint( '    -t <-1 or 0>, --type=<-1 or 0> ' )
        eprint( '        for range (-1,1) use -1' )
        eprint( '        for range ( 0,1) use  0' )
        eprint( '    -f coeff_file, --file=coeff_file' )
        eprint( '    -p param_file, --params=param_file' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        
        params = None
            
        try:                                
            opts, args = getopt.getopt( argv, 'hcf:p:t:',
                                        ['help','clip', 'file=',
                                         'param=', 'type='] )    
        except getopt.GetoptError as e:
            eprint( 'cnorm: ' + str(e) )
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            ######## param file
            if opt in ( '-p', '--param' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'cnorm: cannot find parameter file:', arg,
                            ' ...exiting' )
                    sys.exit( 2 )
                    
                params = arg

            ######### input file
            elif opt in ( '-f', '--file' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'cnorm: cannot find coefficient file:', arg,
                            ' ...exiting' )
                    sys.exit( 2 )
                    
                self.p.filepath = arg

            ######### clip
            elif opt in ( '-c', '--clip' ):
                self.p.clip = True

            ######### range type
            elif opt in ( '-t', '--type' ):
                
                if arg in ( '-1, 0' ):
                    self.p.ntype = int( arg )
                else:
                    eprint( 'cnorm: bad normalization type', arg, ' ...exiting')
                    sys.exit( 2 )
 
        if params == None and self.p.filepath == '':
            
            eprint( 'cnorm: no coefficient file given ... exiting' )
            self.usage()
            sys.exit( 2 )
   
        if params != None:
            
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'cnorm: set_params: cannot read parameter file:',
                        params, ' ...exiting' )
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
