#! /usr/bin/env python
'''
@file render.py
@author Scott L. Williams
@package POLI
@brief writes a numpy data array into an image file.
@LICENSE
#
#  render.py Copyright (C) 2010-2026 Scott L. Williams.
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

# poli sink operator that renders data array into an image format.
# user selects source buffers to render, either grey level with LUT or RGB.

render_copyright = 'render.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import getopt
import numpy as np
from pio import pio
from PIL import Image
from ezprint import eprint

# determine if graphics can be enabled
try:
    import wx
    from op_panel import op_panel
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
# if not, then assume non-graphics implementation
except:
    from op import op
    operator = op
    #eprint( 'render: using non-graphics mode.' )
       
# return an instance of 'render' class 
def instantiate():	
#    return render( get_name() )
    return render()

def get_name(): 
    return 'render'

class render_parameters( pio ):       # hold arguments values here
    
    def __init__( self ):
        
        self.filepath = ''
        self.RGB = False

        # if RGB = True
        self.redbuf = 0
        self.grnbuf = 1
        self.blubuf = 2

        # if RGB = False
        self.greybuf = 0

        # pass through buffers ( for command line implementation )
        self.passthru = False

        self.verbose = True
        
        phome = os.environ['POLI_HOME']
        self.lutfile = phome + '/luts/ramp.lut'

    def print_params( self ):

        eprint( '\nparameters for render:' )
        eprint( '       output filepath =', self.filepath )
        eprint( '          lut filepath =', self.lutfile )
        eprint( '              RGB type =', self.RGB )
        eprint( '               red buf =', self.redbuf )
        eprint( '             green buf =', self.grnbuf )
        eprint( '              blue buf =', self.blubuf )
        eprint( '              grey buf =', self.greybuf )
        eprint( '               verbose =', self.verbose )
        eprint( '              passthru =', self.passthru )

#-----------------------------------------------------------------------------

# render data into an image format of 3-bands, RGB or grey levels
class render( operator ):
    
    def __init__( self ):

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = render_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '    numpy =', np.version.version )

    # convert single-banded image to byte datatype for display
    def recast_band( self, image ):

        if image.dtype == bool:
            image = image*255
            
        # check for constant values
        nmin = np.nanmin(image)         # get values to scale
        nmax = np.nanmax(image)         # ignoring nan
        if nmax == nmin : 
            scale = 0.0 	        # make blank image
            c = 0.0
        else:
            scale = 255.0/(nmax-nmin)   # stretch to 8-bit range
            c = -scale*nmin

        # test for NaN, replace with minimum value
        image[ np.isnan(image) ] = nmin
 
        b_image = (image*scale + c).astype(np.uint8)
        return b_image

    def readlut( self, filename ):

        try:
            lutfile = open( filename, 'r' )
        except:
            eprint( self.name + ': cannot read lut file:', filename )
            return None
        
        lut  = np.empty( (256,3), dtype=np.uint8 )
      
        i = 0
        for line in lutfile:
            r,g,b = line.split(',')
            lut[i,0] = int( r.strip() )
            lut[i,1] = int( g.strip() )
            lut[i,2] = int( b.strip() )
            i += 1

        self.p.lutfile = filename
        lutfile.close()

        return lut

    def render_band( self, index ):

        lut = self.readlut( self.p.lutfile )
        if isinstance( lut, type(None) ):
            return
        
        if self.source.dtype == np.uint8:   # check if source data is byte
            image = self.source[:,:,index]  # use directly
        else:
            image = self.recast_band( self.source[:,:,index] ) # make byte

        self.sink = lut[ image ] # run through lut filter

    # merge three bands into a color display
    def render_merged( self, r, g, b ):
        
        # check if data type is byte
        if self.source.dtype == np.uint8:

            # use view directly
            self.sink[:,:,0] = self.source[:,:,r]
            self.sink[:,:,1] = self.source[:,:,g]
            self.sink[:,:,2] = self.source[:,:,b]
        else:
            self.sink[:,:,0] = self.recast_band( self.source[:,:,r] )
            self.sink[:,:,1] = self.recast_band( self.source[:,:,g] )
            self.sink[:,:,2] = self.recast_band( self.source[:,:,b] )

    def run( self ):

        if self.p.verbose:
            self.p.print_params()               # report parameters used
            self.print_versions()
        
        if self.p.filepath == '':
            eprint( self.name + ': output filename not set...returning' )
            return
        
        height,width,nbands = self.source.shape
        self.sink = np.zeros( (height,width,3), dtype=np.uint8 )
        
        # create color image based on given buffers
        if self.p.RGB == True:
            if nbands < 3:
                eprint( self.name + \
                        ': not enough source bands to make color image' )
                return

            # check if given rgb bands are ok
            if self.p.redbuf >= nbands or \
               self.p.grnbuf >= nbands or \
               self.p.blubuf >= nbands:
                eprint( self.name + ': color band outside range' )
                return
            
            self.render_merged( self.p.redbuf, 
                                self.p.grnbuf, 
                                self.p.blubuf )

        # create grey level image 
        else:
            if self.p.greybuf >= nbands :
                eprint( self.name + ': grey band outside range' )
                return

            self.render_band( self.p.greybuf  )
        
        # output image
        pil = Image.new('RGB', (width, height) )
        pil.frombytes( self.sink.tobytes())
        try:
            pil.save( self.p.filepath )
        except:
            eprint( self.name + ': cannot write to file:', self.p.filepath )
        
    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters

        # update params class
        redbuf = int( self.t_redbuf.GetValue().strip() )
        if redbuf < 0:
            eprint( self.name + ': read_params_from_panel:' )
            eprint( '        red buffer must be > 0' )
            eprint( '       ...returning' )
            return False
 
        blubuf = int( self.t_bluebuf.GetValue().strip() )
        if blubuf < 0:
            eprint( self.name + ': read_params_from_panel:' )
            eprint( '        blue buffer must be > 0' )
            eprint( '       ...returning' )
            return False
 
        grnbuf = int( self.t_greenbuf.GetValue().strip() )
        if grnbuf < 0:
            eprint( self.name + ': read_params_from_panel:' )
            eprint( '        green buffer must be > 0' )
            eprint( '       ...returning' )
            return False
 
        greybuf = int( self.t_greybuf.GetValue().strip() )
        if greybuf < 0:
            eprint( self.name + ': read_params_from_panel:' )
            eprint( '        grey buffer must be > 0' )
            eprint( '       ...returning' )
            return False
      
        lutfile = self.t_lut_filepath.GetValue().strip()
        if not os.path.isfile( lutfile ):
            eprint( self.name + ': read_params_from_panel:' )
            eprint( '        file cannot be found:', lutfile )
            eprint( '        ...returning' )
            return False

        self.p.redbuf = redbuf
        self.p.blubuf = blubuf
        self.p.grnbuf = grnbuf
        self.p.greybuf= greybuf
        self.p.lutfile= lutfile
        
        self.p.filepath = self.t_filepath.GetValue().strip()

        return True
        
    def write_params_to_panel( self ):   # write parameters to panel

        # fill in buffer and filepath values
        self.t_redbuf.SetValue( str( self.p.redbuf ) )
        self.t_greenbuf.SetValue( str( self.p.grnbuf ) )
        self.t_bluebuf.SetValue( str( self.p.blubuf ) )
        self.t_greybuf.SetValue( str( self.p.greybuf ) )

        self.t_lut_filepath.SetValue( self.p.lutfile )
        self.t_filepath.SetValue( self.p.filepath )
        
        if self.p.RGB == True:
            self.r_color.SetValue( True )

            self.l_redbuf.Enable( True )
            self.t_redbuf.Enable( True )

            self.l_greenbuf.Enable( True )
            self.t_greenbuf.Enable( True )

            self.l_bluebuf.Enable( True )
            self.t_bluebuf.Enable( True )

            self.l_greybuf.Enable( False )
            self.t_greybuf.Enable( False )

            self.l_lut_prompt.Enable( False )
            self.t_lut_filepath.Enable( False )
            self.b_browse.Enable( False )
            
        else:
            self.r_grey.SetValue( True )

            self.l_redbuf.Enable( False )
            self.t_redbuf.Enable( False )

            self.l_greenbuf.Enable( False )
            self.t_greenbuf.Enable( False )

            self.l_bluebuf.Enable( False )
            self.t_bluebuf.Enable( False )

            self.l_greybuf.Enable( True )
            self.t_greybuf.Enable( True )

            self.l_lut_prompt.Enable( True )
            self.t_lut_filepath.Enable( True )
            self.b_browse.Enable( True )
 
    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( (1,10) )  # add space

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        panel = self.radio_panel()
        h_sizer.Add( panel, 0, wx.ALL, 1)
        h_sizer.Add( (1,50) )  # add space

        vv_sizer =  wx.BoxSizer( wx.VERTICAL )
        panel = self.rgb_panel()
        vv_sizer.Add( panel )
        vv_sizer.Add( 30,25 )

        panel = self.grey_panel()
        vv_sizer.Add( panel )

        h_sizer.Add( vv_sizer )

        v_sizer.Add( h_sizer )
        
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( (4, 1) ) # spacer from left

        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 'enter output filepath:' )

        h_sizer.Add( prompt, 0, wx.TOP, 1 )  # lower prompt
        v_sizer.Add( h_sizer, 1 ) #, wx.EXPAND )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        self.t_filepath = wx.TextCtrl( self.p_client, -1 )
        self.t_filepath.SetToolTip( 'enter image out filepath' )
        h_sizer.Add(  self.t_filepath, wx.EXPAND )

        # browse directory button
        b_browse = wx.Button( self.p_client, -1, 'browse' )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        b_browse.SetToolTip( 'browse directories for data file' )
        h_sizer.Add( b_browse )

        h_sizer.Add( (1, 1),1 ) # '1' pushes button to right       
 
        v_sizer.Add( h_sizer, 1 ) #, wx.EXPAND )
        #v_sizer.Add( self.t_filepath, 1, wx.EXPAND )
        
        self.p_client.SetSizer( v_sizer )

        # populate with default values
        self.write_params_to_panel()

    def radio_panel( self ):

        p_radio = wx.Panel( self.p_client, -1 )
        sizer = wx.GridSizer( 4, 2, 1, 1 )

        self.r_color = wx.RadioButton( p_radio, -1, 'color', 
                                          style = wx.RB_GROUP )
        self.r_color.Bind( wx.EVT_RADIOBUTTON, self.on_color )
        
        self.r_grey = wx.RadioButton( p_radio, -1, 'grey' )
        self.r_grey.Bind( wx.EVT_RADIOBUTTON, self.on_grey )
        
        sizer.Add( self.r_color )
        sizer.Add( 1,1 )
        sizer.Add( 1,1 )
        sizer.Add( 1,1 )
        sizer.Add( self.r_grey )
        sizer.Add( 1,1 )
        
        p_radio.SetSizer( sizer )
        return p_radio

    def rgb_panel( self ):

        p_rgb = wx.Panel( self.p_client, -1 )
        sizer = wx.GridSizer( 1, 8, 1, 1 )

        # red 
        self.l_redbuf = wx.StaticText( p_rgb, -1, 'r=' )
        self.t_redbuf = wx.TextCtrl( p_rgb, -1, '0', size=(35,25),
                                     style=wx.ALIGN_RIGHT )
        self.t_redbuf.SetToolTip( 'enter band number for red' )
        sizer.Add( self.l_redbuf )
        sizer.Add( self.t_redbuf )
        sizer.Add (1,1)

        # green 
        self.l_greenbuf = wx.StaticText( p_rgb, -1, 'g=' )
        self.t_greenbuf = wx.TextCtrl( p_rgb, -1, '1', size=(35,25),
                                       style=wx.ALIGN_RIGHT )
        self.t_greenbuf.SetToolTip( 'enter band number for green' )
        sizer.Add( self.l_greenbuf )
        sizer.Add( self.t_greenbuf )
        sizer.Add (1,1)

        # blue
        self.l_bluebuf = wx.StaticText( p_rgb, -1, 'b=' )
        self.t_bluebuf = wx.TextCtrl( p_rgb, -1, '2', size=(35,25),
                                      style=wx.ALIGN_RIGHT )
                                      
        self.t_bluebuf.SetToolTip( 'enter band number for blue' )
        sizer.Add( self.l_bluebuf )
        sizer.Add( self.t_bluebuf )
        
        p_rgb.SetSizer( sizer )
        return p_rgb

    def grey_panel( self ):

        p_grey = wx.Panel( self.p_client, -1 )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        
        sizer = wx.GridSizer( 1, 2, 1, 1 )

        # grey
        self.l_greybuf = wx.StaticText( p_grey, -1, 'g=' )
        self.t_greybuf = wx.TextCtrl( p_grey, -1, '0', size=(35,25),
                                      style=wx.ALIGN_RIGHT )

        self.t_greybuf.SetToolTip( 'enter band number for grey' )
        sizer.Add( self.l_greybuf )
        sizer.Add( self.t_greybuf )
        h_sizer.Add( sizer )
        h_sizer.Add( 40,1 )

        self.l_lut_prompt = wx.StaticText( p_grey, -1, 'enter LUT filepath:' )
        h_sizer.Add( self.l_lut_prompt )
        h_sizer.Add( 10,1 )
        
        self.t_lut_filepath = wx.TextCtrl( p_grey, -1, size=(250,25),
                                           style=wx.ALIGN_RIGHT )
        self.t_lut_filepath.SetToolTip( 'enter LUT filepath' )
        h_sizer.Add( self.t_lut_filepath )

        # LUT browse directory button
        self.b_browse = wx.Button( p_grey, -1, 'browse' )
        self.b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        self.b_browse.SetToolTip( 'browse directory for LUT file' )
        h_sizer.Add( (1, 1),1 ) # '1' pushes button to right       
        h_sizer.Add( self.b_browse )
       
        p_grey.SetSizer( h_sizer )
        return p_grey

    # respond to radio color button
    def on_color( self, event ):
        if self.r_color.GetValue():
            self.p.RGB = True
            self.write_params_to_panel()

            
    # respond to radio grey button
    def on_grey( self, event ):
        if self.r_grey.GetValue():
            self.p.RGB = False
            self.write_params_to_panel()

    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, 'Choose a numpy file to read', 
                             os.getcwd(), "", "*",
                             style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()


    # respond to file browse click
    def on_lut_browse( self, event ):
        
        dlg = wx.FileDialog( self, 'Choose a LUT file to read', 
                             os.getcwd(), "", "*", style=wx.FD_OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            path = path.strip()
            self.t_lut_filepath.SetValue( path ) # update filename to gui

        dlg.Destroy()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: render.py' )
        eprint( '       -h, --help' )
        eprint( '       -g band, --grey=band' )
        eprint( '       -c b1,b2,b3, --color=b1,b2,b3' )
        eprint( '       -f filepath, --file=filepath' )
        eprint( '       -l lutfile, --lut=lutfile' )
        eprint( '       -t, --thru, # enable buffers passthru ' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin', 'output is filename' )
        sys.exit( 1 )

    def set_params( self, argv ):
        
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 'htg:c:f:l:', 
                                        ['help','thru','grey=','color=','file=',
                                         'lut='] )
        except getopt.GetoptError as e:
            eprint( self.name + ': ' + str(e) )
            self.usage()                          
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                
            if opt in ( '-l', '--lut' ):
                
                if not os.path.isfile( arg ):
                    eprint( self.name + ': lut file does not exist...exiting' )
                    self.usage()
                self.p.lutfile = arg
  
            elif opt in ( '-g', '--grey' ):

                if int( arg ) < 0:
                    eprint( self.name + \
                            ': band cannot be less than zero...exiting' )
                    self.usage()
                self.p.greybuf = int( arg )
                self.p.RGB = False
                
            elif opt in ( '-c', '--color' ):
                
                clist = arg.split(',')
                self.p.redbuf = int( clist[0] )
                self.p.grnbuf = int( clist[1] )
                self.p.blubuf = int( clist[2] )
                
                if self.p.redbuf < 0 or \
                   self.p.grnbuf < 0 or \
                   self.p.blubuf < 0:
                    eprint( self.name + ': band cannot be less than zero' )
                    usage()
                    
                self.p.RGB = True

            elif opt in ( '-f', '--file' ):
                self.p.filepath = arg

            elif opt in ( '-t', '--thru' ):
                self.p.passthru = True  # only for command line
            
            elif opt in ( '-p', '--params' ):
                params = arg
  
        if self.p.filepath == '' and params == None :
            
          eprint( name + ': set_params: no output filename given' )
          sys.exit( 2 )

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( self.name + ': set_params: bad params file read' )
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
        if oper.p.passthru:
            oper.sink.dump( sys.stdout.buffer )
  
    except Exception as e:
        eprint( str(e) )
