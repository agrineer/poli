#! /usr/bin/env python

'''
@file notch.py
@author Scott L. Williams.
@package POLI
@brief notch bands out of input source 
@LICENSE
#  notch.py
# 
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
@sections DESCRIPTION
notch bands from input 
'''
# embed copyright in binary
notch_copyright = 'notch.py Copyright (c) 2010-2026 Scott L. Williams ' + \
                  'released under GNU GPL V3.0'

# notch out bands 
# TODO: notch in bands also

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
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
# if not then assume non-graphics implementaion
except:
    from op import op
    operator = op
    #eprint( 'notch: using non-graphics mode.' )
    
def get_name():
    return 'notch'

# return an instance of 'notch' class 
# without having to know its name
def instantiate():	
    return notch()

class notch_parameters( pio ):
    def __init__( self ):
        self.pass_string = ''

    def print_params( self ):
        
        eprint( '\nparameters for notch:' )
        eprint( '          pass string =', self.pass_string )
 
class notch( op_panel ):
    
    def __init__( self ): # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__  
        self.p = notch_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )
 
    def str2tuple(self, s):
        # convert tuple-like strings to real tuples.
        # eg '1,2,3,4' -> (1, 2, 3, 4)

        s = s.strip()                 # remove trailing white space

        # check for dangling ','
        if s[-1] == ',':
            s = s[:-1]

        items = s.split(',')

        # clean up spaces, convert to ints
        u = [ x.replace(' ', '') for x in items ] # clean up spaces
        t = [ int(x) for x in items ]
        
        return tuple( t )

    def run( self ):            # override superclass run

        self.p.print_params()        # report parameters as op is run
        self.print_versions()

        height,width,nbands = self.source.shape
        if nbands == 1 :
            eprint( 'notch: input must have more than one band...returning' )
            return

        if len( self.p.pass_string ) < 1:
            eprint( 'notch: pass string is empty...returning' )
            return

        self.notchbands = self.str2tuple( self.p.pass_string )

        if len( self.notchbands ) < 1:
            eprint( 'notch: pass string is invalid:',self.p.pass_string,
                    '...returning' )
            return
            
        for i in self.notchbands:
            if i < 0 or i > (nbands-1):
                eprint( 'notch: band=', i, 'is out of range' )
                return None

        newnbands = nbands - len( self.notchbands )
        self.sink = np.empty( (height,width,newnbands), self.source.dtype )

        j = 0
        for i in range(0,nbands):
            if i not in self.notchbands:
                self.sink[:,:,j] = self.source[:,:,i]
                j += 1

    ####################################################################
    # gui section
    ####################################################################

    # overide to grab neighbor's band tags
    def apply_work( self ):

        # get input image from a neighbor operator
        self.source = self.get_source( 1 )
        
        if not isinstance( self.source, np.ndarray ):
            eprint( 'notch: apply_work: ' + \
                    'neighbor sink (output) image not set' )
            return
        
        self.set_areal_tags( 1 )        # inherit nav and band tags
        self.run()                      # run the operator

        if not isinstance( self.sink, np.ndarray ):
            return

        neighbor = self.benchtop.op.index( self )-1
        neighbor_tags = self.benchtop.op[neighbor].band_tags
        if neighbor_tags == None:
            return

        # copy over tag strings
        j = 0
        nbands = self.source.shape[2]
        self.band_tags = []
        for i in range(0,nbands):
            if i not in self.notchbands:
                self.band_tags.append( neighbor_tags[i] )
                j += 1

    # scan panel parameters
    def read_params_from_panel( self ):
        self.p.pass_string = self.t_pass_string.GetValue()
        return True

    # write parameters to panel
    def write_params_to_panel( self ):
        self.t_pass_string.SetValue( self.p.pass_string )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )

        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 
                                'enter bands (0-indexed) to notch out:' )

        v_sizer.Add( prompt, 0, wx.TOP, 8 )  # prompt

        self.t_pass_string = wx.TextCtrl( self.p_client, -1 )
        self.t_pass_string.SetToolTip( 'comma delimited string' +
                                       ' eg 0,4,8 and are 0 indexed' )

        # keep this bind since we have only one parameter
        self.t_pass_string.Bind( wx.EVT_KEY_DOWN, self.on_file_key) 
        v_sizer.Add( self.t_pass_string, 1, wx.EXPAND )

        self.p_client.SetSizer( v_sizer )

        self.write_params_to_panel()

    # intercept keystroke; look for CR
    def on_file_key( self, event ):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:   
            self.on_apply( None )     # as if pressing 'apply'
        event.Skip()                  # pass along event
        
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( 'usage: notch.py' )
        eprint( '       -h, --help' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( '       -s pass_string, --string=pass_string' )
        eprint( 'param file overrides line arguments' )
        eprint( 'input is stdin, output is stdout' )
        sys.exit( 2 )  
 
    def set_params( self, argv ):
         
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hp:s:', ['help','param=','string='])
        except getopt.GetoptError as e:
            eprint( str(e) )
            usage()                          
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                usage()                     
                
            elif opt in ( '-p', '--params' ):
                params = arg
                
            elif opt in ( '-s', '--string' ):
                self.p.pass_string = arg    

        if params == None and self.params.pass_string == '':
            eprint( 'notch: no pass string or params file given...exiting' )
            usage()

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( 'notch: set_params: bad params file read...exiting' )
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
