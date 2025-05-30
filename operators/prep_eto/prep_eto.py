#! /usr/bin/env python3

'''
@file prep_eto.py
@author Scott L. Williams.
@package POLI
@brief Convert raw variables from WRF output to actual ETo variable and average.
@LICENSE
#
#  Copyright (C) 2016-2025 Scott L. Williams.
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
read wrf derived buffers and prepare data for calculating
standard reference evapotranspiration, ETo. time scale is 1 day
'''

prep_eto_copyright = 'prep_eto.py Copyright (c) 2016-2025 Scott L. Williams, released under GNU GPL V3.0'

import os 
import sys
import glob
import math
import getopt
import netCDF4
import datetime
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
    eprint( 'prep_eto: using non-graphics mode.' )

def get_name():                
    return 'prep_eto'

# return an instance of 'prep_eto' class 
def instantiate():
    return prep_eto( get_name() )

class prep_eto_parameters( pio ):   # hold arguments values here
    
    def __init__( self ):
        self.albedo = 0.23 # radiation constants for green grass
        self.emiss = 0.97
        self.domain = 3
        self.rundate = 20241205
        self.dirpath = '/home/agrineer/wrf/output/ANDES03'
 
    def print_params( self ) :
        
        eprint( '\nparameters for prep_eto:' )
        eprint( '    albedo =', self.albedo )
        eprint( '     emiss =', self.emiss )
        eprint( '    domain =', self.domain )
        eprint( '   dirpath =', self.dirpath )
        eprint( '   rundate =', self.rundate )

# ------------------------------------------------------------------------

class prep_eto( operator ):
    
    def __init__( self, name ): # initialize op_panel but no graphics
        
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__
        self.p = prep_eto_parameters()
        
    def print_versions( self ):
        eprint( '\nusing versions:' )
        eprint( '  ', self.name,'=', self.__version__ )
        eprint( '      numpy =', np.version.version )
        eprint( '    netCDF4 =', netCDF4.__version__ )
               
    ## Convert wind speed from given height to 2 meters
    def convert_wind( self, w, h ):
        factor = 4.87/math.log(67.8*h - 5.42)  # Eq. 47 FAO paper No.56
        return w*factor


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
        num = 4098.0*( 0.6108*np.exp(17.27*Thc/(Thc+237.3)) )
        denom = (Thc+237.3)**2

        return num/denom

    ## Calculate net radiation
    ## @param Rsd - downward shortwave radiation ( W/m^2 ) (buffer array)
    ## @param Rld - downward longwave radiation ( W/m^2 )  (buffer array)
    ## @param tsk - skin temperature ( k )                 (buffer array)
    ## @param albedo - grass short wave reflection coefficient   (scaler)
    ## @param emiss  - grass radiation emmisivity coefficient    (scaler )
    def calc_Rn( self, Rsd, Rld, tsk, albedo, emiss ):

        # Calculate net radiation
           
        # we start with naive net radiation, Rn = Rsd*(1-a) + Rld - Rlu
        # later enhancements may include additional components
        # see chp. 3 of FAO paper 56 on deriving Rlu from air temp, Ea, and
        # cloudiness. Eq. 39
 
        # NOTE: cumulus physics option is used in wrf namelist.input file
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
        Rlu = emiss*sigma*(tsk**4)    # upward long wave   

        # radiation toward surface is positive
        # radiation away from surface is negative
        # Rld == GLW
        # Rsd == SWDOWN
                                                  
        Rn = (1.0-albedo)*Rsd + Rld - Rlu  
        
        # convert (J/s)/m^2 to  (MJ/(m^2 * hr)
        # return Rn/(10**6) * 3600.0
        return Rn * 0.0036    # same as above

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

        numy,numx,nbands = wvars.shape # get dimensions

        # allocate output buffer; has 8 bands
        prep = np.empty( (numy,numx,8), dtype=np.float32 )

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

    # parses out variable time slice, and if 4D, the level
    def str2list( self, s ): 

        self.buf = []
        self.tband = []               # time bands
        self.lband = []               # level bands
        
        items = s.split(',')          

        u = [x.replace(' ', '') for x in items] # clean up spaces
        
        self.nbuf = len( u )                    # keep nbuf for later
        
        for x in u:
            
            items = x.split(':')
            self.buf.append( items[0] )
            self.tband.append( int(items[1]) )

            try:
                self.lband.append( int(items[2]) ) # 4D level index
            except:
                self.lband.append( None )
    
    ## Populate a numpy array from wrf file according to bandstr
    def read_wrf( self, infile, bandstr ):

        try:
            ds = netCDF4.Dataset( infile, 'r' ) # open the netcdf file
                
        except Exception as e:
            eprint( str(e) )
            eprint( 'prep_eto: read_wrf: cannot open file:', infile )
            return None

        # decode bandstr for band and time slices
        self.str2list( bandstr )
        time_steps = 24

        # grab data from wrf output
        for i in range( 0, self.nbuf ):

            if self.tband[i] < 0 or self.tband[i] >= time_steps:
                eprint( 'prep_eto: read_wrf: bad time index:', tbands[i] )
                return None

            # read 3D or 4D buffer
            if self.lband[i] == None:
                data = ds.variables[ self.buf[i] ][ self.tband[i] ] # 3D
            else:
                # extract from 4-D buffer (eg.atmospheric levels)
                data = ds.variables[self.buf[i]][self.tband[i]][self.lband[i]]
                
            # make output buffer now that we have shape
            if i == 0:
                ny,nx = data.shape
                wvars = np.empty( (ny, nx, self.nbuf), dtype=data.dtype )

            wvars[:,:,i] = data # put data in output array

        return wvars
    
    def run( self ):            

        self.p.print_params()            # report parameters used when running
        self.print_versions()

        '''
        # date housekeeping
        yr = int( self.p.date[:4] )
        mn = int( self.p.date[4:6] )
        dy = int( self.p.date[6:8] )
        
        # instantiate date objects
        rday = datetime.date( yr, mn, dy )         # run date
        rfile = self.check_file( rday )
        if rfile == None:
            return
        
        yday = rday - datetime.timedelta( days=1 ) # run date's yesterday
        yfile = self.check_file( yday )
        if yfile == None:
            return
        '''
        
        # initiate hourly averages by getting yesterday's
        # last time slice values
        bandstr =  'TSK:23,SWDOWN:23,GLW:23,GRDFLX:23,' + \
                   'T2:23,PSFC:23,Q2:23,U10:23,V10:23'

        wraw = self.read_wrf( self.yfile, bandstr )
        if not isinstance( wraw, np.ndarray ):
            return
        
        last = self.prep_eto( wraw )
        if not isinstance( last, np.ndarray ):
            return
 
        # make the output based on the Y,X shape
        numy = last.shape[0]
        numx = last.shape[1]
        temp = np.empty( (numy,numx,194), dtype=np.float32 ) # includes nav data
   
        # iterate time steps to get hourly ETo variable averages
        for i in range( 0, 24 ):

            # generate band input string to extract buffers from wrf netCDF 
            bandstr =  'TSK:'    + str(i)   + \
                      ',SWDOWN:' + str(i)   + \
                      ',GLW:'    + str(i)   + \
                      ',GRDFLX:' + str(i)   + \
                      ',T2:'     + str(i)   + \
                      ',PSFC:'   + str(i)   + \
                      ',Q2:'     + str(i)   + \
                      ',U10:'    + str(i)   + \
                      ',V10:'    + str(i)

            wraw = self.read_wrf( self.rfile, bandstr )
            if not isinstance( wraw, np.ndarray ):
                return

            hour = self.prep_eto( wraw )
             
            temp[:,:,i*8:i*8+8] = (last + hour)/2.0
            last = hour

        # read lat/long data
        lat = self.read_wrf( self.rfile, 'XLAT:0' )
        if not isinstance( lat, np.ndarray ):
            eprint( 'prep_eto: run: cannot read latitude data...returning' )
            return
 
        temp[:,:,192] = np.reshape( lat, (numy,numx) ) # tack on the end

        lon = self.read_wrf( self.rfile, 'XLONG:0' )
        if not isinstance( lon, np.ndarray ):
            eprint( 'prep_eto: run: cannot read longitdue data...returning' )
            return
 
        temp[:,:,193] = np.reshape( lon, (numy,numx) )
   
        self.sink = np.flip( temp, 0 ) # netCDF4 gives upside down data
        
    ####################################################################
    # gui section
    ####################################################################

    # overide since we are a source (kinda)
    def apply_work( self ):
        
        self.run()            # run the operator

        # check if valid run output
        if not isinstance( self.sink, np.ndarray ):
            eprint( 'prep_eto: run output buffer not valid...returning' )
            return
        
        self.areal_index = None # reset areal to center image

        # we have shape, dtype; make nav data buffer
        numy,numx,nbands = self.sink.shape
        self.nav_data = np.empty( (numy,numx,2), dtype=self.sink.dtype )
        
        # load latitudes and longitudes
        self.nav_data[:,:,0] = self.sink[:,:,nbands-2]  
        self.nav_data[:,:,1] = self.sink[:,:,nbands-1]
  
        num = self.sink.shape[2] - 2        # exclude lat/long buffers
        hours = int(num/8 )
                
        # set up buffer tags
        tags = [ 'Rn MJ/(m**2 hr)',
                 'G  MJ/(m**2 hr)',
                 'T  C',
                 'D  kPa/C',
                 'g  kPa/C',
                 'es kPa',
                 'ea kPa',
                 'W2 m/s' ]

        self.band_tags = []
        for i in range(hours):
            self.band_tags.extend( tags )

        # nav tags
        self.band_tags.extend( 'lat' )
        self.band_tags.extend( 'lon' )
        
        self.nav_tags = ['lat','lon']

    def read_params_from_panel( self ):       # scan panel parameters
                                              # and do prelimary error checks
        albedo = self.t_albedo.GetValue().strip()
        if not self.check_albedo( albedo ):
            return False
        
        emiss = self.t_emiss.GetValue().strip()
        if not self.check_emiss( emiss ):
            return False 
   
        domain = self.t_domain.GetValue().strip()
        if not self.check_domain( domain ):
            return False

        rundate = self.t_rundate.GetValue().strip()
        if not self.check_rundate( rundate ):
            return False
        
        dirpath = self.t_dirpath.GetValue().strip()
        if not self.check_dirpath( dirpath ):
            return False

        # one more check...and get filepaths
        yfile, rfile = self.check_wrf_files( dirpath, domain, rundate )
        if yfile == None:
            return False
        
        # update parameters
        self.p.albedo = float(albedo)
        self.p.emiss = float(emiss)
        self.p.domain = int(domain)
        self.p.rundate = rundate
        self.p.dirpath = dirpath

        self.yfile = yfile
        self.rfile = rfile
        
        return True
    
    def write_params_to_panel( self ):        # write parameters to panel
        
        self.t_albedo.SetValue( str( self.p.albedo ) )
        self.t_emiss.SetValue( str( self.p.emiss ) )
        self.t_domain.SetValue( str( self.p.domain ) )
        self.t_dirpath.SetValue( str( self.p.dirpath ) )
        self.t_rundate.SetValue( str( self.p.rundate ) )
    
    # initialize graphics
    def init_panel( self, benchtop ):

        operator.init_panel( self, benchtop ) # start with basics

        # this panel's boxer only vertical box
        v_sizer = wx.BoxSizer( wx.VERTICAL )
 
        # values subpanel
        panel = self.values_panel()
        v_sizer.Add( panel )
        v_sizer.Add( 1,5 )

        panel = self.dirpath_panel()
        v_sizer.Add( panel, 1, wx.EXPAND )

        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    # make panel for albedo and date values
    def values_panel( self ):
        
        p_values = wx.Panel( self.p_client, -1 )

        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( 1,5 )

        # domain input text control
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( 4, 1 ) # spacer from left

        # first value input text control
        prompt = wx.StaticText( p_values, -1, 'domain number:                   ' )
        h_sizer.Add( prompt )
        h_sizer.Add( 5, 1 )
        
        self.t_domain = wx.TextCtrl( p_values, -1, '', style=wx.ALIGN_RIGHT,
                                     size=(40,20) )
        
        self.t_domain.SetToolTip( 'domain number must be >= 1' )

        h_sizer.Add( self.t_domain )
        v_sizer.Add( h_sizer )
        v_sizer.AddSpacer( 5 )
   
        # albedo input text control
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.AddSpacer( 4 ) # spacer from left

        prompt = wx.StaticText( p_values, -1,
                                'grass albedo:                          ' )
        h_sizer.Add( prompt )
        h_sizer.AddSpacer( 5 )
        
        self.t_albedo = wx.TextCtrl( p_values, -1, '', style=wx.ALIGN_RIGHT,
                                     size=(40,20) )
        
        self.t_albedo.SetToolTip( 'grass albedo value can be specified' +
                                  ' in range 0-1; however the default is 0.23' +
                                  ' with small variances. you can vary this' +
                                  ' to see the effect on ETo' )
        
        h_sizer.Add( self.t_albedo )
        v_sizer.Add( h_sizer )
        v_sizer.AddSpacer( 5 )

        # emissivity input text control
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.AddSpacer( 4 ) # spacer from left

        # first value input text control
        prompt = wx.StaticText( p_values, -1,
                                'grass emissivity:                    ' )
        h_sizer.Add( prompt )
        h_sizer.AddSpacer( 5 )
        
        self.t_emiss = wx.TextCtrl( p_values, -1, '', style=wx.ALIGN_RIGHT,
                                     size=(40,20) )
        
        self.t_emiss.SetToolTip( 'grass emissivity value can be specified' +
                                  ' in range 0-1; however the default is 0.97' +
                                  ' with small variances. you can vary this' +
                                  ' to see the effect on ETo' )
        
        h_sizer.Add( self.t_emiss )
        v_sizer.Add( h_sizer )
        v_sizer.AddSpacer( 5 )

        # date text control
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.Add( 4, 1 ) # spacer from left

        prompt = wx.StaticText( p_values, -1, 'date (YYYYMMDD):  ' )
        h_sizer.Add( prompt )
        h_sizer.AddSpacer( 5 )
        
        self.t_rundate = wx.TextCtrl( p_values, -1, '', style=wx.ALIGN_RIGHT,
                                      size=(75,20) )
        
        self.t_rundate.SetToolTip( 'WRF run date in YYYYMMDD format' )
        h_sizer.Add( self.t_rundate )
        v_sizer.Add( h_sizer )
               
        p_values.SetSizer( v_sizer )
        return p_values
 
    # make panel for directory path
    def dirpath_panel( self ):
        
        p_dirpath = wx.Panel( self.p_client, -1 )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        h_sizer.AddSpacer( 4 ) # spacer from left

        # file input text control
        prompt = wx.StaticText( p_dirpath, -1, 'enter WRF directory path:' )
        h_sizer.Add( prompt )
        h_sizer.AddSpacer( 10 )
        
        self.t_dirpath = wx.TextCtrl( p_dirpath, -1, '' )
        self.t_dirpath.SetToolTip( 'directory path for WRF dates' )
        h_sizer.Add( self.t_dirpath, 1, wx.EXPAND )
        h_sizer.AddSpacer( 3 )
        
        b_browse = wx.Button( p_dirpath, -1, 'browse' )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )
        h_sizer.Add( b_browse )
        
        p_dirpath.SetSizer( h_sizer )
        return p_dirpath
    
    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.DirDialog( self, "Choose a WRF directory", os.getcwd() )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath().strip()
            self.t_dirpath.SetValue( path ) # update dir path 

        dlg.Destroy()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
                
        eprint( 'usage: prep_eto' )
        eprint( '     -h, --help' )
        eprint( '     -a albedo, --albedo=albedo note: value must be 0-1' )
        eprint( '     -e emiss, --emiss=emiss note: value must be 0-1' )
        eprint( '     -d domain, --domain=domain note: value must be > 0' )
        eprint( '     -r YYYYMMDD, --rundate=YYYYMMDD' )
        eprint( '     -w dirpath, --where=dirpath' )
        eprint( '     -p paramfile, --param=paramfile' )
        eprint( 'param file overrides line argument' )
        eprint( 'output is stdout' )
        sys.exit( 2 )  

    def check_albedo( self, a ):

        try:
            albedo = float( a )
        except:
            eprint( 'prep_eto: cannot interpret albedo as a float...returning' )
            return False
        
        if (albedo < 0) or (albedo > 1.0):
            eprint( 'prep_eto: bad albedo value:', a )
            eprint( '          must be in range: 0-1...returning' )
            return False
        
        return True

    def check_emiss( self, e ):

        try:
            emiss = float( e )
        except:
            eprint( 'prep_eto: cannot interpret emissivity as a float' +
                    '...returning' )
            return False

        if (emiss < 0) or (emiss > 1.0):
            eprint( 'prep_eto: bad emissivity value:', e )
            eprint( '          must be in range: 0-1...returning' )
            return False
        
        return True

    def check_domain( self, d ):

        try:
            domain = int( d )
        except:
            eprint( 'prep_eto: cannot interpret domain as an int:', d,
                    ' returning' )
            return False

        if (domain < 1) or (domain > 3):
            eprint( 'prep_eto: domain must be in range 1-3 ... returning' )
            return False
        
        return True
                
    def check_rundate( self, rundate ):

        if not len( rundate ) == 8:
            eprint( 'prep_eto: must be 8 digits...returning' )
            return False
  
        try:
            test = int( rundate )
        except:
            eprint( 'prep_eto: rundate cannot be interpreted as an integer' +
                    '...returning' )
            return False
        
        return True

    def check_dirpath( self, dirpath ):
        
        if not os.path.isdir( dirpath ):
            eprint( 'prep_eto: WRF input directory:', dirpath,
                    ' does not exist...returning' )
            return False
        
        return True

    # check if WRF file exist
    def check_file( self, dirpath, domain, day ):

        ddir = dirpath + '/' + day.strftime( '%Y%m%d/' )
        name = ddir + 'wrfout_d' + '%02d'%int(domain) + \
               day.strftime( "_%Y-%m-%d" ) + '*'
        eprint( 'prep_eto: looking for file:', name )

        # use glob since start hour can vary
        dfile = glob.glob( name )
        lnames = len( dfile )
        
        if lnames == 0:
            eprint( 'prep_eto: file:', name, 'cannot be found...returning' )
            return None
        
        if lnames > 1:           
            eprint( 'prep_eto: too many files, must be only 1...returning' )
            return None
        
        if not os.path.isfile( dfile[0] ):
            eprint( 'prep_eto: file:', rfile[0],
                    'cannot be found...returning' )
            return None

        eprint( 'prep_eto: found file:', dfile[0] )
        return dfile[0]

    def check_wrf_files( self, dirpath, domain, rundate ):

        yr = int( rundate[:4] )
        mn = int( rundate[4:6] )
        dy = int( rundate[6:8] )

        # instantiate date objects
        rday = datetime.date( yr, mn, dy )         # run date
        rfile = self.check_file( dirpath, domain, rday )
        if rfile == None:
           return None, None

        yday = rday - datetime.timedelta( days=1 ) # run date's yesterday
        yfile = self.check_file( dirpath, domain, yday )
        if yfile == None:
            return None, None

        return yfile, rfile
     
    def set_arg_values( self, albedo, emiss, domain, dirpath, rundate ):

        # albedo
        if not albedo == None:
            if not self.check_albedo( albedo ):
                return False
            self.p.albedo = float( albedo )

        # emissivity
        if not emiss == None:
            if not self.check_emiss( emiss ):
                return False
            self.p.emiss = float( emiss )
        
        # domain
        if not domain == None:
            if not self.check_domain( domain ):
                return False
            self.p.domain = int( domain )

        # WRF dirpath
        if dirpath == None:
            eprint( 'prep_eto: please specify the WRF directory' )
            return False
        else:
            if not self.check_dirpath( dirpath ):
                return False
        
        # rundate
        if rundate == None:
            eprint( 'prep_eto: please specify rundate' )
            return False
        else:
            if not self.check_rundate( rundate ):
                return False
            self.p.rundate = rundate
       
        # one more check...
        yfile, rfile = self.check_wrf_files( dirpath, domain, rundate )
        if yfile == None:
            return False

        self.yfile = yfile
        self.rfile = rfile
        
        return True
        
    def set_params( self, argv ):
        
        params = None

        albedo = None
        emiss = None
        domain = None
        dirpath = None
        rundate = None

        try:                                
            opts, args = getopt.getopt( argv,
                                        'ha:e:d:r:w:p:', 
                                        ['help','albedo=', 'emiss=',
                                         'domain=','rundate','where=','param='])
        except getopt.GetoptError:           
            self.usage()              
                  
        for opt, arg in opts:                
            if opt in ( '-h', '--help' ):      
                self.usage()                     

            elif opt in ( '-a', '--albedo' ):
                albedo = arg

            elif opt in ( '-e', '--emiss' ):
                emiss = arg

            elif opt in ( '-d', '--domain' ):
                domain = arg

            elif opt in ( '-w', '--where' ):
                dirpath = arg
               
            elif opt in ( '-r', '--rundate' ):
                rundate = arg
 
            elif opt in ( '-p', '--param' ):
                param = arg
                 
        if params != None:

            # params file overrides arguments 
            ok = self.read_params_from_file( param )
            if not ok:
                eprint( 'prep_eto: set_params: bad param file read...exiting' )
                sys.exit( 2 )
            return
                
        arg_set = self.set_arg_values( albedo, emiss, domain, dirpath, rundate )
        if not arg_set:
            sys.exit( 2 )

####################################################################
# command line user entry point 
####################################################################
if __name__ == '__main__':
    
    oper = instantiate()                  # source point for pipe
    oper.set_params( sys.argv[1:] )
    oper.run()

    # send downstream
    oper.sink.dump( sys.stdout.buffer )
