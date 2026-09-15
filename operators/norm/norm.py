#! /usr/bin/env python

'''
@file norm.py
@author Scott L. Williams
@package POLI
@brief Normalize all bands to either -1 to 1 or 0 to 1.
@LICENSE
#
#  norm.py Copyright (C) 2010-2026 Scott L. Williams.
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
Normalize all bands to either -1 to 1 or 0 to 1.
Optionally report scaling coefficients to file 
Optionally consider interlaced buffers for scaling
'''

norm_copyright = 'norm.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
from ezprint import eprint

# determine if graphics (wxpython) can be enabled
try:
    import wx
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
# if not then assume non-graphics implementation
except:
    from op import op
    operator = op
    #eprint( 'norm: using non-graphics mode.' )

def get_name(): 
    return 'norm'

# return an instance of 'norm' class 
def instantiate():	
    return norm()

class norm_parameters( pio ):              # hold arguments values here
    
    def __init__( self ):        
        self.ntype = 0                # 0 for 0 to 1; -1 for -1 to 1
        self.write = False
        self.skip = 0                 # interlace skip factor
        self.filepath = ''            # coefficient output file

    def print_params( self ):        
        eprint( '\nparameters for norm:' )
        eprint( '                skip =', self.skip )
        eprint( '               ntype =', self.ntype )
        eprint( '            filepath =', self.filepath )
        eprint( '        write coeffs =', self.write )
        
# ---------------------------------------------------------------------------

class norm( operator ):
    
    def __init__( self ):       # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = norm_parameters()
        
        self.cfile = None

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '   ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    def calc_coefficients( self, image, floor, ceiling ):

        # workaround for bug in nanmin wrt unsigned ints
        if image.dtype == np.uint8  \
        or image.dtype == np.uint16 \
        or image.dtype == np.uint32:
            imin = np.min( image )
            imax = np.max( image )
        else:
            imin = np.nanmin( image )         # get values to scale by
            imax = np.nanmax( image )         # ignoring nan

        if imax == imin :                # check for constant values
            scale = 0.0 	         # make image a surface plane
            c = 0.0
   
        elif np.isinf( imin ) or np.isinf( imax ):
            scale = 0.0 	         # make image a surface plane
            c = 0.0

        else:
            scale = (ceiling-floor)/float((imax-imin)) 
            c = floor-scale*imin

        return scale,c
    
    # convert single band value range from floor to ceiling
    def scale_band( self, band, image, floor, ceiling ):

        scale, c = self.calc_coefficients( image, floor, ceiling )
        
        # write out coeffs if asked to
        if ( self.cfile != None ):
            self.cfile.write( '%d,'%band + '%.8f,'%scale + '%.8f\n'%c )
        
        return image*scale + c

    # scale each band independently
    def no_interlace_scale( self ):

        nbands = self.source.shape[2]
        for i in range( nbands ):
            self.sink[:,:,i] = self.scale_band( i, self.source[:,:,i],
                                                self.p.ntype, 1.0 )
    # scale interlaced bands together
    def interlace_scale( self ):

        nbands = self.source.shape[2]
        skip = self.p.skip

        # check if skip factor divides evenly into number of buffers
        remainder = nbands%skip
        if remainder != 0:
            eprint( 'norm: skip factor does not evenly divide into number of bands')
            return

        # create appended buffers based on skips
        cnum = int(nbands/skip)      # num of buffers to combine
        
        for i in range( skip ):  

            tmp = self.source[:,:,i] # initialize first buffer

            # append remaining buffers
            for j in range( 1, cnum ):
                tmp = np.append( tmp, self.source[:,:,i+(skip*j)] )
         
            scale, c = self.calc_coefficients( tmp, self.p.ntype, 1.0 )
            
            # scale the interlaced buffers
            for j in range( 0, cnum ):
                index = i + (skip*j)
                self.sink[:,:, index] = self.source[:,:,index]*scale + c

                # write out coeffs if asked to
                if ( self.cfile != None ):
                    self.cfile.write( '%d,'%index + '%.8f,'%scale + '%.8f\n'%c )

    def run( self ):

        if (self.p.filepath == '') and (self.p.write == True ):
            eprint( 'norm: run: filepath not set...returning' )
            return
        
        self.p.print_params()   # report parameters used when running
        self.print_versions()
         
        # create the output buffer to populate with scaled values
        height,width,nbands = self.source.shape
        self.sink = np.empty( (height,width,nbands), dtype=np.float32 )

        # write out band coeffs? open file and set header
        if self.p.write:
            self.cfile = open( self.p.filepath, 'w' )

            # report number of bands and range type
            self.cfile.write( '%d,'%nbands+'%d\n'%self.p.ntype ) 

        if self.p.skip == 0:
            self.no_interlace_scale()
        else:
            self.interlace_scale()
            
        if self.cfile != None:
            self.cfile.close()
            
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):     # scan panel parameters

        # get interlace skip factor
        skip = int( self.t_skip.GetValue().strip() )
        if skip < 0:
            eprint( 'norm: read_params_from_panel:' )
            eprint( '      skip should be >= 0' )
            eprint( '      returning' )
            return False
        
        self.p.skip = skip
        
        # normalization type
        if self.r_positive.GetValue():
            self.p.ntype = 0
        else:
            self.p.ntype = -1

        # write enable
        if self.c_write.GetValue():
            self.p.write = True
        else:
            self.p.write = False

        # set filename to use
        self.p.filepath = self.t_filepath.GetValue()

        return True
     
    def write_params_to_panel( self ):       # write parameters to panel
        
        # normalization type
        if self.p.ntype == 0:
            self.r_positive.SetValue( True )
        else:
            self.r_negative.SetValue( True )

        # write enable
        if self.p.write:
            self.c_write.SetValue( True )
            self.t_filepath.Enable( True )
            self.fprompt.Enable( True )
            self.b_browse.Enable( True )
            
        else:
            self.c_write.SetValue( False )
            self.t_filepath.Enable( False ) 
            self.fprompt.Enable( False )
            self.b_browse.Enable( False )
 
        # write filepath
        self.t_filepath.SetValue( self.p.filepath )

        # set interlace skip factor
        self.t_skip.SetValue( str( self.p.skip ) )
             
    # initialize panel graphics
    def init_panel( self, benchtop ):

        # FIXME: needs better layout format
        operator.init_panel( self, benchtop ) # start with basics

        # make parameter input boxes
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        
        panel = self.type_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1 )

        panel = self.skip_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1 )
        v_sizer.Add( h_sizer, 1 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
 
        panel = self.write_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1 )
        v_sizer.Add( h_sizer, 1 )

        self.p_client.SetSizer( v_sizer )

        # populate with default values
        self.write_params_to_panel()

    def type_panel( self ):

        p_type = wx.Panel( self.p_client, -1 ) #, style=wx.SUNKEN_BORDER )

        sizer = wx.GridSizer( 3, 2, 1, 1 )
        prompt = wx.StaticText( p_type, -1, 'normalization type:' )
        sizer.Add( prompt )
        sizer.Add( (1,1) )

        self.r_positive = wx.RadioButton( p_type, -1, '0 to 1', 
                                          style = wx.RB_GROUP )
        sizer.Add( self.r_positive )
 
        self.r_negative = wx.RadioButton( p_type, -1, '-1 to 1' )
        sizer.Add( self.r_negative )
        
        p_type.SetSizer( sizer )
        
        return p_type
    
    def skip_panel( self ):

        p_skip = wx.Panel( self.p_client, -1 ) #, style=wx.SUNKEN_BORDER )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        
        prompt = wx.StaticText( p_skip, -1, 'interlace buffer skip factor:' )
        v_sizer.Add( prompt )
        v_sizer.Add( (0,10) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        
        prompt = wx.StaticText( p_skip, -1, 'skip:' )
        h_sizer.Add( prompt )
        h_sizer.Add( (10,0) )

        self.t_skip = wx.TextCtrl( p_skip, -1, '',size=(50,20) )
        h_sizer.Add( self.t_skip )
 
        v_sizer.Add( h_sizer )
        
        p_skip.SetSizer( v_sizer )
        
        return p_skip

    def write_panel( self ):
        
        p_write = wx.Panel( self.p_client, -1 ) #, style=wx.SUNKEN_BORDER )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        prompt = wx.StaticText( p_write, -1, 'write normalization coefficients to file:' )
        v_sizer.Add( prompt )
        v_sizer.Add( (10,20) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        self.c_write = wx.CheckBox( p_write, -1, 'coeffs to file')
        self.c_write.Bind( wx.EVT_CHECKBOX, self.on_write )             
        self.c_write.SetToolTip( 'enable writing coefficients to file' )

        h_sizer.Add( self.c_write )
        h_sizer.Add( (50,1) )

        # file input text control
        self.fprompt = wx.StaticText( p_write, -1, 'enter coeff filepath:' )
        h_sizer.Add( self.fprompt )
        
        self.t_filepath = wx.TextCtrl( p_write, -1, '' ) #, size=(500,20) )
        self.t_filepath.SetToolTip( 'enter filepath for norm coefficients' )
        h_sizer.Add( self.t_filepath, wx.EXPAND )

        # browse directory button
        self.b_browse = wx.Button( p_write, -1, 'browse' )
        self.b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        self.b_browse.SetToolTip( 'browse directory for data file' )
        h_sizer.Add( (1, 1),1 ) # '1' pushes button to right       
        h_sizer.Add( self.b_browse )

        v_sizer.Add( h_sizer )
        
        p_write.SetSizer( v_sizer )
        
        return p_write

    def on_write( self, event ):        # respond to write checkbox
        
        if self.c_write.GetValue():
            
            # enable file text box
            self.t_filepath.Enable( True )
            self.fprompt.Enable( True )
            self.b_browse.Enable( True )
        else:
            
            # disable file text box
            self.t_filepath.Enable( False )
            self.fprompt.Enable( False )
            self.b_browse.Enable( False )
 
    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, 'Enter a coefficient filepath to write', 
                             os.getcwd(), "", "*",
                             style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

    ############################################################
    # command line options for batch implementation
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: norm.py' )
        eprint( '       -h, --help' )
        eprint( '       -f coeff_file --file=coeff_file' )
        eprint( '       -t [0,-1], --type=[0,-1]' )
        eprint( '       -s skip_factor, --skip=skip_factor' )
        eprint( '       -p param_file, --params=param_file' )
        eprint( '       input is stdin, output is stdout' )
        sys.exit(1)

    def set_params( self, argv ):
        
        params = None
        
        try:                                
            opts, args = getopt.getopt( argv, 'hf:t:s:p:',
                                        ['help','file=','type=',
                                         'skip','param='] )
            
        except getopt.GetoptError as e:
            eprint( 'norm: '+ str(e) )
            self.usage()                    
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                
            elif opt in ( '-f', '--file' ):  # output coeff file
                self.p.filepath = arg
                self.p.write = True
                
            elif opt in ( '-t', '--type' ):
                if arg in ('-1','0' ):
                    self.p.ntype = int( arg )
                else:
                    eprint( 'norm: unknown type:', arg,
                            'must be -1 or 0 ...exiting' )
                    sys.exit( 2 )
                
            elif opt in ( '-s', '--skip' ):
                self.p.skip = int( arg )
                
            elif opt in ('-p', '--params'):
                params = arg

        # over rides other parameters
        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( "norm: cannot read parameter file" )
                sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':

    try:
        import tempfile

        # read from stdin to temporary file
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
