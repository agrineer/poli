#! /usr/bin/env /usr/bin/python

#  notch.py
# 
#  Copyright (C) 2010 Scott L. Williams.
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

######## TODO: rename this operator pass_thru and make a real notch operator

# embed copyright in binary
poli_copyright = 'notch.py Copyright (c) 2010 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'

# notch out bands 
# TODO: notch in bands also

import wx
import sys
import getopt

import numpy as np

from op_panel import op_panel

# return an instance of 'notch' class 
# without having to know its name
def instantiate():	
    return notch( get_name() )

def get_name():
    return 'notch'

class notch_parameters():
    def __init__( self ):
        self.pass_string = ''

class notch( op_panel ):
    def __init__( self, name ): # initialize op_panel but no graphics
        self.op_id = 'notch version 0.0'
        self.params = notch_parameters()
        op_panel.__init__( self, name )
        
    def str2tuple(self, s):
        # convert tuple-like strings to real tuples.
        # eg '1,2,3,4' -> (1, 2, 3, 4)
        
        items = s.split(',')

        # clean up spaces, convert to ints
        t = [int(x.strip()) for x in items] 
        return tuple( t )

    def run( self ):            # override superclass run

        height,width,nbands = self.source.shape
        if nbands == 1 :
            print 'notch: image must have more than one band'
            return None

        if len(self.params.pass_string) == 0:
            print 'notch: pass string is empty'
            return None

        self.notchbands = self.str2tuple( self.params.pass_string )

        for i in self.notchbands:
            if i < 0 or i > (nbands-1):
                print 'notch: band=', 'is out of range'
                return None

        newnbands = nbands - len(self.notchbands)
        self.sink = np.empty( (height,width,newnbands), self.source.dtype )

        j = 0
        for i in range(nbands):
            if i not in self.notchbands:
                self.sink[:,:,j] = self.source[:,:,i]
                j += 1

    # overide since we need to handle
    # thread slightly different ( add labels )
    def apply_work( self ):

        # get input image from a neighbor operator
        self.source = self.get_source( 1 )
        if self.source == None:  # is neighbor sink image set? 

            print 'op_panel:apply_work: ' + \
                  'neighbor sink (output) image not set'
            return

        self.set_areal_tags( 1 ) # inherit nav and band tags
        self.run()               # run the operator

        if self.sink == None:
            return

        neighbor = self.benchtop.op.index( self )-1
        neighbor_tags = self.benchtop.op[neighbor].band_tags
        j = 0
        nbands = self.source.shape[2]
        self.band_tags = []
        for i in range(nbands):
            if i not in self.notchbands:
                self.band_tags.append( neighbor_tags[i] )
                j += 1

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        print >> sys.stderr, 'usage: notch.py'
        print >> sys.stderr, '       -h, --help'
        print >> sys.stderr, '       -p paramfile, --params=paramfile'
        print >> sys.stderr, '       -s passstring, --string=passstring'
        print >> sys.stderr, '       param file overrides line arguments'
        print >> sys.stderr, '       input is stdin, output is stdout'

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'hp:s:', ['help','param=','string='])
        except getopt.GetoptError:           
            usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                usage()                     
                sys.exit(0)                  
            elif opt in ( '-p', '--params' ):
                params = arg  
            elif opt in ( '-s', '--string' ):
                self.params.pass_string = arg    

        if params == None and self.params.pass_string == None:
            print >> sys.stderr, \
                'notch: warning: no pass string given'

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                sys.exit( 2 )

    ####################################################################
    # gui section
    ####################################################################

    # scan panel parameters
    def read_params_from_panel( self ):
        self.params.pass_string = self.t_pass_string.GetValue()

    # write parameters to panel
    def write_params_to_panel( self ):
        self.t_pass_string.SetValue( self.params.pass_string )

    # initialize graphics
    def init_panel( self, benchtop ):
        op_panel.init_panel( self, benchtop ) # start with basics

        v_sizer = wx.BoxSizer( wx.VERTICAL )

        # file input text control
        prompt = wx.StaticText( self.p_client, -1, 
                                'enter bands to notch out:' )

        v_sizer.Add( prompt, 0, wx.TOP, 8 )  # prompt

        self.t_pass_string = wx.TextCtrl( self.p_client, -1 )
        self.t_pass_string.SetToolTipString( 'comma delimited string eg 1,4,8' )
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

####################################################################
# command line user entry point 
####################################################################

if __name__ == '__main__':             
    oper = instantiate()                  
    oper.set_params( sys.argv[1:] )
    oper.run()            
    oper.sink.dump( sys.stdout )      
