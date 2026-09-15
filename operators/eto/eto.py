#! /usr/bin/env python

'''
@file eto.py
@author Scott L. Williams
@package POLI
@brief Calculates standard evaporation (ETo).
@LICENSE
#
#  Copyright (C) 2016-2026 Scott L. Williams.
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

# calculate standard reference evapotranspiration
# and attach lat and long buffers

eto_copyright = 'eto.py Copyright (c) 2016-2026 Scott L. Williams ' + \
                 'released under GNU GPL V3.0'
import os
import sys
import math
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
    
# if not then assume non-graphics implementation
except:
    from op import op
    operator = op
    #eprint( 'eto: using non-graphics mode.' )

def get_name(): 
    return 'eto'

# return an instance of 'preeto' class 
# without having to know its name
def instantiate():	
    return eto()

class eto_parameters( pio ):
    def __init__( self ):
        self.nav = False

    def print_params( self ):
        eprint( '\nparameters for eto:' )
        eprint( '         navigation =', self.nav  )

# ---------------------------------------------------------------------------

class eto( operator ):           # calculate_eto operator

    def __init__( self ):        # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = eto_parameters()
        
    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '   numpy =', np.version.version, '\n' )
 
    # implement eq. 53 from FAO #56 hourly example
    ## Calculate ETo using eq. 53 in Chapter 4 from FAO paper #56 hourly example
    ## http://www.fao.org/docrep/X0490E/x0490e08.htm
    ## @param Rn  - net radiation, MJ/(m**2*hr) eq.40
    ## @param G   - soil flux,MJ/(m**2*hr) eq.45,46
    ## @param Thc - mean hourly air temperature, C
    ## @param D   - saturation slope vapour pressure curve at Thc, kPa/C, eq. 13
    ## @param g   - psychrometric, kPa/C, eq.8
    ## @param es  - saturation vapor pressure at Thc,kPa,eq.11
    ## @param ea  - average hourly actual vapor pressure, kPa, eq.54
    ## @param w2  - average hourly wind speed at 2m, m/s

    def calc_et_ref( self,
                     Rn,      # net radiation, MJ/(m**2*hr) eq.40
                     G,       # soil flux,MJ/(m**2*hr) eq.45,46
                     Thc,     # mean hourly air temperature, C
                     D,       # saturation slope vapour pressure curve 
                              # at Th, kPa/C, eq. 13
                     g,       # psychrometric, kPa/C, eq.8
                     es,      # saturation vapor pressure at Th,kPa,eq.11
                     ea,      # average hourly actual vapor pressure, kPa, eq.54
                     w2 ):    # average hourly wind speed at 2m, m/s


        # calculate numerator from eq.53
        num_a = 0.408*D*(Rn-G)
        num_b = g*(37.0/(Thc+273.16))
        num_c = w2*(es-ea)

        num = num_a + num_b*num_c

        # calculate denominator from eq.53
        denom = D + g*(1 + 0.34*w2)
        eto = num/denom

        return( eto.clip( 0.0, None) ) # no negative values

        # FAO hourly method can give negative values. These likely
        # indicate surface dew. Experience (comparisons) indicates 
        # clipping negative values gives better alignment with daily
        # interval calculation

        return num/denom

    # end calc_et_ref

    def run( self ):                   

        self.p.print_params()          # report parameters used when running
        self.print_versions()

        # make some preliminary checks
 
        # data type; is this needed?
        if self.source.dtype != np.float32:
            eprint( 'wrong data type, should be float32' )
            return

        numy,numx,nbands = self.source.shape # get dimensions

        # input bands:
        # Rn     hourly averaged net radiation,            MJ/(m**2*hr)
        # G      hourly averaged ground heat flux,         MJ/(m**2*hr)
        # Thk    hourly averaged temperature,              C
        # D      saturation slope vapor pressure curve,    kPa/C
        # g      psychrometric from mean surface pressure, kPa/C
        # es,    saturation vapor pressure at Thc,         kPa
        # ea,    actual vapor pressure,                    kPa
        # w2,    wind speed,                               m/s

        if nbands != 194:  # 24 hrs*8 + 2 (lat/lon)
            eprint( 'eto: wrong band size, should be 194, got:',
                   nbands, ' ...returning' )
            return

        # allocate output space
        if self.p.nav:
            eto = np.zeros( (numy,numx,3), dtype=np.float32 )
        else:
            eto = np.zeros( (numy,numx,1), dtype=np.float32 )
 
        for i in range( 0, 24 ):
 
            temp = self.calc_et_ref( self.source[:,:,0],
                                     self.source[:,:,1],
                                     self.source[:,:,2],
                                     self.source[:,:,3],
                                     self.source[:,:,4],
                                     self.source[:,:,5],
                                     self.source[:,:,6],
                                     self.source[:,:,7] )
            
            # accumulate hourly values
            eto[:,:,0] += temp 

        # tack on lat/lon buffers
        if self.p.nav:
            eto[:,:,1] = self.source[:,:,192]
            eto[:,:,2] = self.source[:,:,193]

        self.sink = eto
       
        self.band_tags = ['ETo mm/hr', 'lat', 'lon']

    ####################################################################
    # gui section
    ####################################################################
    def read_params_from_panel( self ):       # scan panel parameters
        self.p.nav = self.c_nav.GetValue()
        return True

    def write_params_to_panel( self ):        # write parameters to panel
        self.c_nav_SetValue( self.p.nav )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # show panel
        v_sizer = wx.BoxSizer( wx.VERTICAL )

        self.c_nav = wx.CheckBox( self.p_client, 0, 'append lat/lon')
        self.c_nav.SetToolTip( 'lat and long buffer are added if True' )
        
        v_sizer.Add( self.c_nav )
        self.p_client.SetSizer( v_sizer )
 
    ############################################################
    # command line options
    ############################################################

    # TODO: implement direct numpy file read
    
    def usage( self ):

        eprint( 'usage: eto' )
        eprint( '       -h, --help' )
        eprint( '       -n, --nav append latlon buffers' )
        eprint( 'input is stdin, output is stdout', file=sys.stderr )

    def set_params( self, argv ):
    
        try:                                
            opts, args = getopt.getopt( argv, 'hn', ['help','nav'] )
        except getopt.GetoptError:           
            self.usage()              
            sys.exit( 2 )  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )
                
            if opt in ( '-n', '--nav' ):      
                self.p.nav = True       


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

