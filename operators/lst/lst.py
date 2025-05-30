#! /usr/bin/env python3

'''
@file lst.py
@author Scott L. Williams.
@package POLI
@brief calculate land surface temperature using different methods
@LICENSE

#  lst.py
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
@sections DESCRIPTION
# land surface temperature operator for poli 
# for avhrr lst = 1.035*ch4 + 3.048*(ch4-ch5) - 10.74 McClain (1983)
# from Di and Rundquist (1994), He et. al. (1987)
'''

lst_copyright = 'lst.py Copyright (c) 2010-2025 Scott L. Williams ' + \
                'released under GNU GPL V3.0'
import os
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
    eprint( 'lst: using non-graphics mode.' )

def get_name(): 
    return 'lst'

# return an instance of 'lst' class 
def instantiate():	
    return lst( get_name() )

class lst_parameters( pio ):       # hold arguments values here
    
    def __init__( self ):
        self.therm1 = 3            # bands to use (0-indexed) AVHRR default
        self.therm2 = 4
        self.method = 'phulpin'    # options: phulpin, macclain, price, singh

    def print_params( self ):
        
        eprint( '\nparameters for lst:' )
        eprint( '    first  thermal band =', self.therm1 )
        eprint( '    second thermal band =', self.therm2 )
        eprint( '    method              =', self.method )

# ---------------------------------------------------------------------------

class lst( operator ):
    
    def __init__( self, name ):      # initialize op_panel but no graphics
        
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = lst_parameters()

    def print_versions( self ):
        
        eprint( 'using versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version )

    def phulpin( self, t1, t2 ):
        
        # lst = 2.626*ch4 - 1.626*ch5 - 1.1 in Kelvin
        # Phulpin (1980)
        term1 = self.source[:,:,t1]*2.626
        term2 = self.source[:,:,t2]*1.626
        self.sink = term1 - term2 - 1.1
 
    def macclain( self, t1, t2 ):

        # lst = 1.035*ch4 + 3.048*(ch4-ch5) - 10.74 in Kelvin
        # McClain (1983)
        term1 = self.source[:,:,t1]*1.035
        term2 = (self.source[:,:,t1] - self.source[:,:,t2]) * 3.048 
        self.sink = term1 + term2 - 10.74

    def price( self, t1, t2 ):
    
        # lst = ch4 + 3.33(ch4-ch5) in Kelvin
        # Price (1984)
        term1 = self.source[:,:,t1]
        term2 = (self.source[:,:,t1] - self.source[:,:,t2]) * 3.33        
        self.sink = term1 + term2

    def singh( self, t1, t2 ):
    
        # lst = 1.699*ch4 - 0.699*ch5 - 0.240 in Kelvin
        # Singh (1984)
        term1 = self.source[:,:,t1]*1.699
        term2 = self.source[:,:,t2]*0.699
        self.sink = term1 - term2 - 0.240

    def run( self ):                 

        self.p.print_params()            # report parameters used when running
        self.print_versions()
        
        height,width,nbands = self.source.shape

        # check if band is in range       
        if  self.p.therm1 < 0 or self.p.therm1 >= nbands:
            eprint( 'lst: bad first thermal band value=', self.p.therm1,
                    ' ...returning' )
            self.sink = None
            return

        t1 = self.p.therm1

        if  self.p.therm2 < 0 or self.p.therm2 >= nbands:
            eprint( 'lst: bad second thermal band value=', self.p.therm2,
                    ' ...returning' ) 
            self.sink = None
            return
 
        t2 = self.p.therm2

        if self.p.method == 'phulpin':
            self.phulpin( t1, t2 )
            
        elif self.p.method == 'macclain':
            self.macclain( t1, t2 )

        elif self.p.method == 'price':
            self.price( t1, t2 )

        elif self.p.method == 'singh':
            self.singh( t1, t2 )

        else:
            eprint( 'lst: run: unknown method...returning' )
 
        self.sink.shape = height,width,1   # make it 3-d

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):  # scan panel parameters
        
        therm1 = int( self.t_t1.GetValue().strip() )
        if therm1 < 0:
            eprint( 'lst: read_params_from_panel:' )
            eprint( '     first thermal band cannot be < 0' )
            eprint( '     ...returning' )
            return False
            
        therm2 = int( self.t_t2.GetValue().strip() )
        if therm2 < 0:
            eprint( 'lst: read_params_from_panel:' )
            eprint( '     second thermal band cannot be < 0' )
            eprint( '     ...returning' )
            return False
        
        self.p.therm1 = therm1
        self.p.therm2 = therm2

        if self.r_phulpin.GetValue():
            self.p.method = 'phulpin'

        if self.r_macclain.GetValue():
            self.p.method = 'macclain'

        if self.r_price.GetValue():
            self.p.method = 'price'

        if self.r_singh.GetValue():
            self.p.method = 'singh'

        return True
       
    def write_params_to_panel( self ):   # write parameters to panel
        
        t1 = str( self.p.therm1 )
        self.t_t1.SetValue( t1 )
        
        t2 = str( self.p.therm2 )
        self.t_t2.SetValue( t2 )

        if self.p.method == 'phulpin':
            self.r_phulpin.SetValue( True )

        elif self.p.method == 'macclain':
            self.r_macclain.SetValue( True )

        elif self.p.method == 'price':
            self.r_price.SetValue( True )

        elif self.p.method == 'singh':
            self.r_singh.SetValue( True )

        else:
            eprint( 'lst: write_params_to_panel: unknown method:',
                    self.p.method )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1,10 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL) 
        prompt = wx.StaticText( self.p_client, -1, 'thermal1 band:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 10,1 )
        self.t_t1 = wx.TextCtrl( self.p_client, -1, '',
                                 size=(30,20), style=wx.ALIGN_RIGHT )
        #self.t_t1.Bind( wx.EVT_KEY_DOWN, self.on_file_key) 
        self.t_t1.SetToolTip( 'enter band number for first thermal band')
        h_sizer.Add( self.t_t1 )
                 
        v_sizer.Add( h_sizer )
        v_sizer.Add( 1,10 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL)                
        prompt = wx.StaticText( self.p_client, -1, 'thermal2 band:' )
        h_sizer.Add( prompt )
        h_sizer.Add( 10,1 )

        self.t_t2 = wx.TextCtrl( self.p_client, -1, '',
                                 size=(30,20), style=wx.ALIGN_RIGHT )
        #self.t_t2.Bind( wx.EVT_KEY_DOWN, self.on_file_key ) 
        self.t_t2.SetToolTip( 'enter band number for second thermal band' )
        h_sizer.Add( self.t_t2 )
        
        v_sizer.Add( h_sizer )
        v_sizer.Add( 1,10 )

        self.r_phulpin = wx.RadioButton( self.p_client, -1, 'Phulpin',
                                         style = wx.RB_GROUP )
        v_sizer.Add( self.r_phulpin )
        v_sizer.Add( (1,1) )

        self.r_macclain = wx.RadioButton( self.p_client, -1, 'MacClain' )
        v_sizer.Add( self.r_macclain )
        v_sizer.Add( (1,1) )

        self.r_price = wx.RadioButton( self.p_client, -1, 'Price' )
        v_sizer.Add( self.r_price )
        v_sizer.Add( (1,1) )
        
        self.r_singh = wx.RadioButton(self. p_client, -1, 'Singh' )
        v_sizer.Add( self.r_singh )
        self.p_client.SetSizer( v_sizer )

        self.write_params_to_panel()

    '''
    # intercept keystroke; look for CR
    def on_file_key( self, event ):
        keycode = event.GetKeyCode()

        if keycode == wx.WXK_RETURN:   
            self.on_apply( None )     # as if pressing 'apply'
        event.Skip()                  # pass along event
    '''
    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        eprint( 'usage: lst' )
        eprint( '       -h, --help' )
        eprint( '       -f band,--ftherm=band' )
        eprint( '       -s band,--stherm=band' )
        eprint( '       -m method, --method=method ')
        eprint( '          where method: phulpin, macclain, price, singh' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( 'param file overrides command line arguments' )
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hf:s:m:p:', 
                                        ['help', 'ftherm=','stherm=',
                                         'method=', 'params='] )
        except getopt.GetoptError:           
            self.usage()                          
            sys.exit(2)  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
                
            elif opt in ( '-f','--ftherm' ):                
                self.p.therm1 = int( arg )
                
            elif opt in ( '-s','--stherm' ):                
                self.p.therm2 = int( arg )

            elif opt in ( '-m','--method' ):
                
                if arg not in ['phulpin','macclain', 'price', 'singh']:
                    eprint( 'lst: set_params: unknown method', arg,
                            ' ...exiting' )
                    sys.exit( 2 )
                self.p.method = arg
                
            elif opt in ('-p', '--params'):
                params = arg  

        if params != None:
            ok = self.read_params_from_file( params )
            if not ok:
                sys.exit(2)
                
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
