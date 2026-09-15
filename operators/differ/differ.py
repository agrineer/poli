#! /usr/bin/env python

'''
@file differ.py
@author Scott L. Williams.
@package POLI
@brief take the difference between two images of same shape
@LICENSE
#
#  differ.py Copyright (C) 2010-2026 Scott L. Williams.
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
differ_copyright = 'differ.py Copyright (c) 2010-2026 Scott L. Williams ' + \
                   'released under GNU GPL V3.0'

# take the difference between two images of same shape.

# first image is the normal source neighbor (n=1), but
# second image is specified as an offset to a predecessor
# image (n=X) OR with a numpy file. In pipe mode the second image is specified

import os
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint

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
    eprint( 'differ: using non-graphics mode.' )

def get_name(): 
    return 'differ'

# return an instance of 'diff' class 
def instantiate():	
    return differ()

class differ_parameters( pio ):        # hold argument values here
    
    def __init__( self ):

        self.use_file = False      # ingest file as extra_source
        self.filepath = ''
        self.xsrc_offset = 2       # top_panel stream offset for extra source  
        self.sqerror = False
        self.apply_on_file_drop = True
        self.absolute = False

        self.fout = sys.stderr     # used for batch ouput, otherwise stderr

    def print_params( self ):
        
        eprint( '\nparameters for differ:' )
        eprint( '               sqerror =', self.sqerror )
        eprint( '              absolute =', self.absolute ) 
        eprint( '              use file =', self.use_file )
        eprint( '            input file =', self.filepath )
        eprint( '       x source offset =', self.xsrc_offset )
        eprint( '    apply on file drop =', self.apply_on_file_drop )
   
# -----------------------------------------------------------------------------

class differ( operator ):
    
    def __init__( self ):      # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = differ_parameters()
        
    def print_versions( self ):       
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    # calculate stats between two images
    def get_stats( self, observed ):       # extra source is observed

        # r**2 = 1 - ss_err/ss_tot 
        # ss_err = residual sum of squares = sum[(yi-fi)**2] for all i
        #                                    y is observed, f is predicted
        # ss_tot = observed sum of squares = sum[(yi-mean)**2] for all i

        # get squared magnitudes of differ image
        self.diff_squared = np.square( self.sink )

        nbands = observed.shape[2]
        for b in range(0,nbands):

            band = observed[:,:,b]     # grab the band image

            # calculate sum of squares (y-ymean)**2          
            band_mean = np.mean( band,              # band mean value
                                 dtype=np.float64 )

            delta_mean = band - band_mean           # difference from mean 
            sq_delta_mean = np.square( delta_mean ) # square differnce
            ss_tot = np.sum( sq_delta_mean )        # tally up
            
	    # calculate sum of squared errors
            ss_err = np.sum( self.diff_squared[:,:,b] )  # already squared 
                                                         # just tally
            rsquare = 1.0 - ss_err/ss_tot

            self.p.fout.write( '%.3f '%rsquare )

        self.p.fout.write( '\n' )

    def run( self ):                 

        self.p.print_params()        # report parameters
        self.print_versions()

        try:
           
            if self.p.use_file:      # load extra source from file
                xsrc = np.load( self.p.filepath, allow_pickle=True )
                                   
            else:                    # load extra source from op_panel stream
                xsrc = self.get_source( self.p.xsrc_offset )

            if not isinstance( xsrc, np.ndarray ):
                eprint( 'differ: extra source is not an ndarray...returning' )
                return
        except:
            eprint( 'differ: could not load extra source data...returning' )
            return
            
        if self.source.shape != xsrc.shape:
            eprint( 'differ: data shapes do not match' )
            eprint( '      source shape=', self.source.shape )
            eprint( '      extra  shape=', self.ex_src.shape )
            return

        # take difference per buffer
        '''
        # count 0.001 as close
        if np.allclose( self.source, xsrc, rtol=0.0, atol=1e-03 ):
            eprint( 'differ: using allclose tolerance of 0.001' )
            self.sink = np.zeros( self.source.shape, dtype=self.source.dtype )
        else:
            self.sink = self.source - xsrc
        '''
        if self.p.absolute:
            self.sink = np.abs( self.source - xsrc.astype( np.float32 ) )
        else:
            # keep negative numbers if any
            self.sink = self.source - xsrc.astype( np.float32 )

        count = np.count_nonzero( self.sink )

        # number pixels =  ny*nx
        npix = xsrc.shape[0]*xsrc.shape[1]
        pcent = (count/float(npix))*100
        eprint( self.name + ': percentage difference = ', '% .2f'%pcent )

        if self.p.sqerror:
            self.get_stats( xsrc )
            self.sink = self.diff_squared

    ####################################################################
    # gui section
    ####################################################################

    def set_filepath( self, obj ):
        
        if isinstance( obj, str ):             # we've been invoked by
            obj.strip()                        # image_tree or file drop
            self.t_filepath.SetValue( obj )
        else:
            eprint( 'YIKES' )
            
        if self.p.apply_on_file_drop:
            self.on_apply( None )

    def read_params_from_panel( self ):  # scan panel parameters

        filepath = self.t_filepath.GetValue().strip()         
        offset = int( self.t_xsrc_offset.GetValue().strip() ) # extra buffer
 
        if self.r_use_file.GetValue():
           if not os.path.isfile( filepath ):
                eprint( 'differ: read_params_from_panel:' )
                eprint( '        file not found:', filepath )
                eprint( '        ...returning' )
                return False
        else:
            if offset < 2:
                eprint( 'differ: read_params_from_panel:' )
                eprint( '        offset must be > 1' )
                eprint( '        ...returning' )
                return False
             
        self.p.use_file = self.r_use_file.GetValue()
        self.p.xsrc_offset = offset
        self.p.filepath = filepath
        
        self.p.sqerror = self.c_sqerror.GetValue()
        self.p.absolute = self.c_absolute.GetValue()
        
        return True

    def write_params_to_panel( self ):   # write parameters to panel
        
        self.t_xsrc_offset.SetValue( str(self.p.xsrc_offset) )
        self.c_sqerror.SetValue( self.p.sqerror )
        self.c_absolute.SetValue( self.p.absolute )

        self.t_filepath.SetValue(  self.p.filepath )
        self.c_apply_on_file_drop.SetValue( self.p.apply_on_file_drop )

        if self.p.use_file:
            self.r_use_file.SetValue( True )
            self.t_filepath.Enable( True )
            self.f_prompt.Enable( True )
            self.b_browse.Enable( True )
            self.t_xsrc_offset.Enable( False )
            self.e_prompt.Enable( False )
            
        else:
            self.r_use_stream.SetValue( True )
            self.t_filepath.Enable( False )
            self.f_prompt.Enable( False )
            self.b_browse.Enable( False )
            self.t_xsrc_offset.Enable( True )
            self.e_prompt.Enable( True )
 
    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1,5 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.c_sqerror = wx.CheckBox( self.p_client, -1, 'square error' )
        h_sizer.Add( self.c_sqerror )
        h_sizer.Add( 10, 1 )

        self.c_absolute = wx.CheckBox( self.p_client, -1, 'absolute' )
        h_sizer.Add( self.c_absolute )
        h_sizer.Add( 10, 1 )

        self.c_apply_on_file_drop = wx.CheckBox( self.p_client, -1,
                                                 'apply on file drop' )
        self.c_apply_on_file_drop.SetToolTip('run operator when file is dropped')
        self.c_apply_on_file_drop.Bind( wx.EVT_LEFT_UP, self.on_drop_click )
 
        h_sizer.Add( 25, 1)
        h_sizer.Add( self.c_apply_on_file_drop )
        v_sizer.Add( h_sizer )
        v_sizer.Add( 1,5 )

        # use operator stream input
        h_sizer = wx.BoxSizer( wx.HORIZONTAL)
        self.r_use_stream = wx.RadioButton( self.p_client, -1,
                                            'use stream offset',
                                            style = wx.RB_GROUP )
        self.r_use_stream.Bind( wx.EVT_LEFT_UP, self.on_radio_click )
 
        h_sizer.Add( self.r_use_stream )
        h_sizer.Add( 10, 18 )

        self.e_prompt = wx.StaticText( self.p_client, -1, 'extra source offset:   ' )
        h_sizer.Add( self.e_prompt )
        self.t_xsrc_offset = wx.TextCtrl( self.p_client, -1, '', size=(30,20),
                                          style=wx.ALIGN_RIGHT )
        h_sizer.Add( self.t_xsrc_offset )

        v_sizer.Add( h_sizer )         
        v_sizer.Add( 1,5 )

        # use file input
        h_sizer = wx.BoxSizer( wx.HORIZONTAL)
        self.r_use_file = wx.RadioButton( self.p_client, -1, 'use file input' )
        self.r_use_file.Bind( wx.EVT_LEFT_UP, self.on_radio_click )
 
        h_sizer.Add( self.r_use_file )
        h_sizer.Add( 40, 1 )

        self.f_prompt = wx.StaticText(self.p_client, -1,'enter numpy filepath:')
        h_sizer.Add( self.f_prompt )

        # filepath
        self.t_filepath = wx.TextCtrl( self.p_client, -1, style= wx.EXPAND )
        self.t_filepath.SetToolTip( 'enter extra source filepath' )
        dt = FileDrop( self.t_filepath, self )   
        self.t_filepath.SetDropTarget( dt )
        h_sizer.Add( self.t_filepath, wx.EXPAND )
        
        # browse directory button
        self.b_browse = wx.Button( self.p_client, -1, 'browse' )
        self.b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        self.b_browse.SetToolTip( 'browse directory for data file' )
        h_sizer.Add( (1, 1),1 ) # '1' pushes button to right       
        h_sizer.Add( self.b_browse )

        v_sizer.Add( h_sizer )
        
        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel() # update panel with default poarameters

    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, 'Choose a numpy file to read', 
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

        if self.r_use_stream.GetValue():
            self.t_filepath.Enable( True )
            self.f_prompt.Enable( True )
            self.t_xsrc_offset.Enable( False )
            self.e_prompt.Enable( False )
            self.b_browse.Enable( True )
            
        else:
            self.t_filepath.Enable( False )
            self.f_prompt.Enable( False ) 
            self.t_xsrc_offset.Enable( True )
            self.e_prompt.Enable( True )
            self.b_browse.Enable( False )
 
    ############################################################
    # command line options for batch implementation 
    ############################################################
    
    def usage( self ):
        eprint( '\nusage: differ.py' )
        eprint( '       -h, --help' )
        eprint( '       -f filepath, --file=filepath note: must be numpy file' )
        eprint( '       -a, --absolute' )
        eprint( '       -s, --sqerror' )
        eprint( '       -p paramfile, --param=paramfile' )
        eprint( 'param file overrides line arguments' )
        sys.exit(1)
        
    def set_params( self, argv ):
        params = None
        self.p.filepath = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hasp:f:',
                                        ['help','absolute','sqerror','param=','file='])
        except getopt.GetoptError as e:
            eprint( 'differ: ' + str(e) )
            self.usage()                          
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )

            elif opt in ( '-s', '--sqerror' ):      
                self.p.sqerror = True

            elif opt in ( '-a', '--absolute' ):      
                self.p.absolute = True
                
            elif opt in ( '-f', '--file' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'differ: cannot find file:', arg, ' ...exiting' )
                    sys.exit( 2 )
                
                self.p.filepath = arg
                self.p.use_file = True

            elif opt in ('-p', '--params'):
                params = arg  

        if params == None and self.p.filepath == None:
            
            eprint( 'differ: no extra source file given ... exiting' )
            self.usage()
            sys.exit( 2 )
  
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':

    try:
        import tempfile

        # numpy needs to 'seek' on the file to load
        # so read from stdin to temporary file
        temp = tempfile.NamedTemporaryFile( delete_on_close=True )
        temp.write( sys.stdin.buffer.read() )
        temp.seek(0,0)

        oper = instantiate()   
        oper.set_params( sys.argv[1:] )

        # load the numpy array data; can use memory map here
        oper.source = np.load( temp, allow_pickle=True )
        oper.run()

        # send down stream 
        oper.sink.dump( sys.stdout.buffer )
  
    except Exception as e:
        eprint( str(e) )
