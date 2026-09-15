#! /usr/bin/env python

'''
@file prep_eto.py
@author Scott L. Williams.
@package POLI
@brief Convert raw variables from WRF output to actual ETo variable and average.
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

# read wrf derived buffers and prepare data for calculating
# standard reference evapotranspiration, ETo
# accepts hours values or can average two hours

# use this operator in conjuction with "wrf_source".

# example wrf_source input string for 11:00hrs :
# TSK:11,SWDOWN:11,GLW:11,GRDFLX:11,T2:11,PSFC:11,Q2:11,U10:11,V10:11
   
prep_eto_copyright = 'prep_eto.py Copyright (c) 2016-2026 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import math
import getopt
import tempfile
import numpy as np
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
    eprint( 'prep_eto: using non-graphics mode.' )

def get_name():                
    return 'prep_eto'

# return an instance of 'prep_eto' class 
def instantiate():
    return prep_eto()   # could just put name here

class prep_eto_parameters():        # hold arguments values here
    def __init__( self ):
        self.albedo = 0.23          # short green grass values for
        self.emiss = 0.97           # albedo and emissity
        self.verbose = False
        self.mmap = True

    def print_params( self ) :
        if self.verbose:
            eprint( '\nparameters for prep_eto:' )
            eprint( '                 verbose =', self.verbose )
            eprint( '                  albedo =', self.albedo )
            eprint( '                   emiss =', self.emiss )
            eprint( '                    mmap =', self.mmap )

# -----------------------------------------------------------

class prep_eto( operator ):
    
    def __init__( self ): # initialize op_panel but no graphics

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = prep_eto_parameters()
        
    def print_versions( self ):
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '      numpy =', np.version.version )

    ## Convert wind speed from given height to 2 meters
    def convert_wind( self, w, h ):
        factor = 4.87/math.log(67.8*h - 5.42)  # Eq. 47 FAO paper No.56
        return w*factor

    ''' TODO: implement this version and compare RH values below
    def RH(self, P,PB,T,QVAPOR):
        #Calculation of relative humidity.
	#Calling sequence WRF_RH = RH(P,PB,T,QVAPOR),
	#where P,PB,T,QVAPOR are standard WRF 3D variables,
	#result WRF_RH is 3D variable on same grid as inputs.
        
        # Formula is from wrf_user.f, vapor
        # https://sourceforge.net/p/vapor/git/ci/7a8986523aee315c9b6b26ab9aa11c702e8938cd/tree/share/python/vapor_wrf.py#l264
	c = 2.0/7.0
	SVP1 = 0.6112
	SVP2 = 17.67
	SVPT0 = 273.15
	SVP3 = 29.65
	EP_3 = 0.622
	TH = T+300.0
	PRESS = P+PB
	TK = TH*np.power(PRESS*.00001,c)
	ES = 10*SVP1*np.exp(SVP2*(TK-SVPT0)/(TK-SVP3))
	QVS = EP_3*ES/(0.01*PRESS - (1.-EP_3)*ES)
	WRF_RH = 100.0*np.maximum(np.minimum(QVAPOR/QVS,1.0),0)
	return WRF_RH
    
    # Calculate relative humidity
    # gives same values as below
    def calc_Rh1( self, Q2, T2, PSFC ):

        #https://archive.eol.ucar.edu/projects/ceop/dm/documents/refdata_report/eqns.html

        TC = T2 - 273.16    # make celsius; per FAO 273.16, not 273.15
        press = 0.01*PSFC   # make millibar

        es = 611.2 * np.exp( (17.67*TC)/(TC + 243.5 ) )
        ea = (Q2*PSFC) / (Q2+0.622 )
        
        Rh = ea/es
        
        return Rh
    '''

    ## Calculate relative humidity at 2m
    ## @param q2 - specific humidity (mixing ratio kg/kg)
    ## @param t2 - temperature at 2m height (K)
    ## @param psfc - surface pressure (Pascal)
    def calc_Rh( self, q2, t2, psfc ):

        # NOTE: can't seem to find or generate relative humidity from WRF!
        #       see README notes for source
        #       update: see above Rh1
    
        # calculate RH
        pq0 = 379.90516
        a2 = 17.2693882
        a3 = 273.16
        a4 = 35.86

        f_rh2 = q2 / ( (pq0 / psfc) * np.exp(a2 * (t2 - a3) / (t2 - a4)) )
        f_rh2 = np.clip( f_rh2, 0.0, 1.0 )

        return f_rh2

    ## Calculate saturation pressure at some temperature C
    ## @param Thc - Temperature array C
    def calc_es( self, Thc ):
        
        # Eq. 11 FAO paper 56
        return 0.6108*np.exp(17.27*Thc/(Thc+237.3))
 
    ## Calculate psychrometric constant, g
    ## @param P - pressure array in Pascals
    def calc_g( self, P ):
        
        # P is in Pascals
        # Eq. 8 FAO paper 56
        return 0.000665*P/1000.0 # return kPa/C

    ## Calculate slope of saturation vapor curve, D
    ## @param Thc - Temperature array C
    def calc_D( self, Thc ):
        
        # Eq. 13 FAO paper 56
        num = 4098.0*(0.6108*np.exp(17.27*Thc/(Thc+237.3)))
        denom = (Thc+237.3)**2

        return num/denom

    ## Calculate net radiation
    ## @param Rsd - downward shortwave radiation
    ## @param Rld - downward longwave radiation
    ## @param tsk - skin temperature ( k )                 (buffer array)
    ## @param emiss  - grass radiation emmisivity coefficient    (scaler )
    ## @param albedo - grass short wave reflection coefficient   (scaler)
    def calc_Rn( self, Rsd, Rld, tsk, emiss, albedo ):

        # Calculate net radiation
           
        # we start with naive net radiation, Rn = Rsd*(1-a) + Rld - Rlu
        # later enhancements may include additional components
        # see chp. 3 of FAO paper 56 on deriving Rlu from air temp, Ea, and
        # cloudiness. Eq. 39
 
        # NOTE: use cumulus physics option in wrf namelist.input file
        #       to reduce radiation due to cloud cover. 

        # use this operationally: net_rad = (sw_in-sw_out) + (lw_in-lw_out)
        # eg. Rn = Rsd*(1-a) + Rld - Rlu

        # calculate upward long wave radiation using Stefan-Boltzmann eq.
        # with given "skin" surface temperature and emissivity values

        sigma = 5.67*10**(-8)  # SI stephan-boltzmann equation constant

        # lotta questions here:
        #   - use grass or soil skin temp?
        #   - tsk should assume soil is wet,
        #   - tsk should assume green grass cover

        # stephan-boltzmann
        # this value is critical and is not general like the atmos loads
        # as skin temperature should be based on hypothetical cover/moisture
        Rlu = emiss*sigma*(tsk**4)      # NOTE: emiss start values, time=0,
                                        #       are not consistent with
                                        #       following ones
                                        # FIXME: implement spinup time
                                        
        # also note that WRF emiss values presumably considers
        # vegetation/soil and not our specific plant (green grass)
        Rn = Rsd*(1.0 - albedo) + Rld - Rlu  # radiation toward surface  +
                                             # radiation away from surface -

        # convert (J/s)/m^2 to  (MJ/(m^2 * hr)
        return Rn/(10**6) * 3600.0

    ## Prepare data buffers for calculating ETo, FAO paper #56 
    ##
    ## input bands:                                                       Band
    ## TSK        surface skin temperature (K)                             0
    ## SWDOWN     downward shortwave at ground (W/m^2)  using gsw          1  
    ## GLW        downward longwave at ground (W/m^2)                      2
    ## GRDFLX     atmospheric heat flux to ground (W/m^2)                  3
    ## T2         temp at 2m (K)                                           4
    ## PSFC       surface pressure (Pa)                                    5
    ## Q2         QV (water vapor mixing ratio) at 2m (kg/kg)              6
    ## U10        wind speed U at 10m (m/s)                                7
    ## V10        wind speed V at 10m (m/s)                                8
    ##
    ## outputs:                                                           Band
    ## Rn  - net radiation, MJ/(m**2*hr) eq.40                             0
    ## G   - soil flux,MJ/(m**2*hr) eq.45,46                               1
    ## Thc - hourly air temperature, C                                     2
    ## D   - saturation slope vapour pressure curve at Thc, kPa/C, eq. 13  3
    ## g   - psychrometric, kPa/C, eq.8                                    4
    ## es  - saturation vapor pressure at Thc,kPa,eq.11                    5
    ## ea  - actual vapor pressure, kPa, eq.54                             6
    ## w2  - hourly wind speed at 2m, m/s                                  7
    ##
    ## @param wvars == numpy buffer holding extracted input variables
    ## @returns numpy buffer holding ETo variable

    def prep_eto( self, wvars ):

        # check data type
        if wvars.dtype != np.float32:
            eprint( 'prep_eto: wrong data type, should be float32' )
            return None

        numy,numx,nbands = wvars.shape # get dimensional values

        # allocate output buffer; has 8 bands
        # and for the 171x171 ETo standard its not necessary
        try:
            if self.p.mmap:

                # set temporary file in /tmp in case we
                # can't mop up stray tmp files
                mmap = tempfile.NamedTemporaryFile( delete_on_close=True )
 
                #prep_mmap = '/tmp/' + tempfile.NamedTemporaryFile()
                prep = np.memmap( mmap, dtype=np.float32, mode='w+',
                                  shape=(numy,numx,8) ) 
                #eprint( 'prep_eto: using memory mapping' )
            else:
                prep = np.empty( shape=(numy,numx,8),dtype=np.float32 )
                #eprint( 'prep_eto: using ram memory' )
                
        except Exception as e:
            eprint( e )
            eprint( 'prep_eto: cannot allocate numpy file...exiting ' ) 
            sys.exit( 1 )

        # pass through skin temperature 
        tsk = wvars[:,:,0]
        
        # downward short and long radiation time slice, W/m^2
        Rsd = wvars[:,:,1]   # SWDOWN
        Rld = wvars[:,:,2]   # GLW

        # calculate net radiation, returns MJ/(m^2*hr)
        prep[:,:,0] = self.calc_Rn( Rsd, Rld, tsk,
                                    self.p.emiss, self.p.albedo )

        # convert the ground flux unit
        G = wvars[:,:,3]
        #prep[:,:,1] = G/(10**6) * 3600  # convert (J/s)/m^2 to MJ/(m^2*hr)
        prep[:,:,1] = G *0.0036         # same as above

        
        # convert temps (K) to (C)
        Thk = wvars[:,:,4]              # T2 (K)
        prep[:,:,2] = Thk - 273.16      # Thc

        # calculate D, saturation slope vapor pressure curve 
        prep[:,:,3] = self.calc_D( prep[:,:,2] )

        # calculate g psychrometric, kPa/C, from surface pressure
        P = wvars[:,:,5]                # PSFC
        prep[:,:,4] = self.calc_g( P )

        # es, saturation vapor pressure at Thc
        prep[:,:,5] = self.calc_es( prep[:,:,2] )

        # calculate relative humidity
        Q2 = wvars[:,:,6]
        Rh = self.calc_Rh( Q2, Thk, P )
            
        # ea, actual vapor pressure, ea = es*Rh
        prep[:,:,6] = prep[:,:,5] * Rh

        # calculate wind speed
        # convert from 10m to 2m speed; m/s
        U2 = self.convert_wind( wvars[:,:,7], 10.0 )
        V2 = self.convert_wind( wvars[:,:,8], 10.0 )
        prep[:,:,7] = np.sqrt( U2*U2 + V2*V2 )

        return prep

    def run( self ):              # override superclass run

        if self.p.verbose:
            self.p.print_params() # report parameters used when running
            self.print_versions()

        self.sink = self.prep_eto( self.source )
                             
        # set up buffer tags
        self.band_tags = [ 'Rn MJ/(m**2 hr)',
                           'G  MJ/(m**2 hr)',
                           'T  C',
                           'D  kPa/C',
                           'g  kPa/C',
                           'es kPa',
                           'ea kPa',
                           'W2 m/s' ]

    ####################################################################
    # gui section
    ####################################################################

    def read_params_from_panel( self ):       # scan panel parameters
        self.p.albedo = float(self.t_albedo.GetValue())
    
    def write_params_to_panel( self ):        # write parameters to panel
        self.t_albedo.SetValue( str(self.p.albedo) )
    
    # initialize graphics
    def init_panel( self, benchtop ):
        operator.init_panel( self, benchtop ) # start with basics
        
        # make parameter input boxes
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        # file input text control for crop albedo
        prompt = wx.StaticText( self.p_client, -1, 
                                'enter albedo value:' )
        h_sizer.Add( prompt, 0, wx.TOP, 8 )  # add prompt

        self.t_albedo = wx.TextCtrl( self.p_client, -1,
                                    style=wx.ALIGN_RIGHT )

        h_sizer.Add( self.t_albedo, 1 )

        v_sizer.Add( h_sizer )
        self.p_client.SetSizer( v_sizer )

        self.write_params_to_panel()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        eprint( 'usage: prep_eto.py' )
        eprint( '       -h, --help' )
        eprint( '       -a albedo_value, --albedo=value' )
        eprint( '       -p paramfile, --params=paramfile' )
        eprint( '       param file overrides line arguments' )
        eprint( '       input is stdin, output is stdout' )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'ha:p:', 
                                        ['help','albedo=', 'param='])
        except getopt.GetoptError:           
            self.usage()              
            sys.exit(2)  
                   
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit(0)                  
            elif opt in ( '-p', '--params' ):
                params = arg      
            elif opt in ( '-a', '--albedo' ):
                self.params.albedo = float(arg)

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
