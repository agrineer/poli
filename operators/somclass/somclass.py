#! /usr/bin/env python

'''
@file somclass.py
@author Scott L. Williams
@package POLI
@brief Read SOM weights and classify data.
@LICENSE
#
#  somclass.py Copyright (C) 2010-2026 Scott L. Williams.
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

# read som weights and classify data

somclass_copyright = 'somclass.py Copyright (c) 2010-2026 Scott L. Williams, released under GNU GPL V3.0'

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
    from filedrop import FileDrop      # drag and drop a file
    operator = op_panel                # uses op_panel in command
                                       # line/batch mode when wx is available
# if not then assume non-graphics implementaion
except:
    from op import op
    operator = op
    #eprint( 'somclass: using non-graphics mode.' )

def get_name(): 
    return 'somclass'

# return an instance of 'somclass' class 
def instantiate():	
    return somclass()

class somclass_parameters( pio ):              # hold arguments values here
    
    def __init__( self ):
        
        self.weightfile = ''
        #self.nclasses = 16
        self.stretch = False
        self.apply_on_file_drop = True
       
    def print_params( self ):
        
        eprint( '\nparameters for somclass:' )
        eprint( '              weightfile =', self.weightfile )
        #eprint( '                nclasses =', self.nclasses )
        eprint( '     stretch grey levels =', self.stretch )
        eprint( '      apply on file drop =', self.apply_on_file_drop )

#------------------------------------------------------------------------------

class somclass( operator ):
    
    def __init__( self ):      # initialize operator

        name = os.path.basename(__file__)
        operator.__init__( self, name )
        self.__version__ = '0.1.0'
        self.op_id = self.name + ' version ' + self.__version__ 
        self.p = somclass_parameters()

    def print_versions( self ):
        
        eprint( '\nusing versions:' )
        eprint( '    ', self.name,'=', self.__version__ )
        eprint( '        numpy =', np.version.version, '\n' )

    # match image sample to closest map weights
    def classify( self, neurons, image ):
        
        num_neurons,nnbands = neurons.shape
        height,width,nbands = image.shape

        if nnbands != nbands:
            eprint('somclass: dimensions do not match:', nnbands, nbands )
            return None

        # set up arrays
        #minn = np.empty( (height,width,1), dtype=np.float32 )
        new = np.empty( (height,width,1), dtype=np.float32 )

        # initialize to the zeroth neuron
        classified = np.zeros( (height,width,1), dtype=np.uint8 )

        diff = image-neurons[0]        # initialize min array
        diff = np.abs( diff )          # using no-square euclid metric
        minn = np.sum( diff, axis=2 )   # TODO: determine metric and use

        skip = int(255/num_neurons)         # stretch out grey levels if asked
        for i in range( 1,num_neurons ):    # test each neuron.
            
            diff = image-neurons[i]         # keep track of minimal distances
            diff = np.abs( diff )           # and compare/adjust with each 
            new = np.sum( diff, axis=2 )    # new distance array

            mask = minn > new                # boolean buffer

            np.putmask( minn, mask, new )           # use same mask to
                                                   # keep track of class
            if self.p.stretch:
                np.putmask( classified, mask, i*skip ) 
            else:
                np.putmask( classified, mask, i ) 

        return classified
    
    '''
    def closest( self, sample, neurons, num, ndims ):

        min_dist = np.inf
        min_index = None
        for i in range( num ):
            
            diff = np.abs( sample - neurons[i] )
            dist = 0
            
            for j in range( ndims ):
                dist += diff[j]
                
            if dist < min_dist:
                min_dist = dist
                min_index = i
            
        return min_index   
    
    # match image sample to closest map weights (the slow way)
    def classify( self, neurons, image ):
        
        num_neurons,nnbands = neurons.shape
        height,width,nbands = image.shape

        if nnbands != nbands:
            eprint('somclass: dimensions do not match:', nnbands, nbands )
            return None

        # initialize to the zeroth neuron
        classified = np.zeros( (height,width,1), dtype=np.uint8 )

        for j in range( height ):
            for i in range( width ):

                classified[j,i,0] = self.closest( image[j,i,:], neurons, num_neurons, nnbands )
                    
        return classified
     '''

    def run( self ):                       # override superclass run

        self.p.print_params()              # report parameters used when running
        self.print_versions()

        # FIXME: split this routine up

        try:                               # read neuron weights
            # get number of classes to read
            #nclasses = self.p.nclasses
            if os.path.isfile( self.p.weightfile ):
                wfile = open( self.p.weightfile, 'r' )
            else:
                eprint( 'somclass: file:', self.p.weightfile,
                        ' is not found...returning' )
                return

            # print header and look for flag
            found = False
            for line in wfile:
                if line.find( 'NEURONS' ) != -1:
                    found = True
                    break
                eprint( line.strip( '\n' ) )
                
            if not found:
                eprint( 'somclass: run: could not find flag' )
                return
                
            nneurons,ndim = wfile.readline().split()
            nneurons = int( nneurons )
            ndim = int( ndim )

            '''
            # see if user request for nclasses works
            if nclasses <= 0:
                nclasses = nneurons # read all classes
                warn = '\tsomclass: reading all classes, nclasses = ' + \
                       str( nneurons ) + '\n'
            else:
                if nclasses > nneurons:
                    warn = '\tsomclass: nclasses given is greater than' + \
                        ' available classes.\n\tsomclass: using all' + \
                        ' available classes. \n\tnclasses= ' + \
                        str(nneurons) + '\n'
                    eprint( warn )
                    nclasses = nneurons
                else:
                    warn = '\tsomclass: using ' + str(nclasses) + \
                        ' classes' + '\n'

            eprint( warn )
            '''
            # get the neuron weights
            neurons = np.empty( (nneurons,ndim), dtype=np.float32 )

            # retrieve neurons from file
            for i in range( nneurons ):            
                line = wfile.readline().split()    # get line components:
                                                   # label weight[0],
                                                   # weight[1],...,
                                                   # number of pixels
                for j in range( 1, ndim+1 ):       # skip grey level label
                    neurons[i,j-1] = float( line[j] )
            
            wfile.close()

        except Exception as e:
            eprint( e )
            self.messages.append( '\tsomclass:run: Exception Error\n' )
            return

        self.sink = self.classify( neurons, self.source )

        # rebranding band here is more convenient than 
        # overriding apply_work()
        self.band_tags = []
        self.band_tags.append( 'som map' )

    ####################################################################
    # gui section
    ####################################################################

    def set_filepath( self, obj ):
        
        if isinstance(obj, str):             # we've been invoked by
            obj.strip()                      # image_tree or file drop
            self.t_filepath.SetValue( obj )
            
        if self.p.apply_on_file_drop:
            self.on_apply( None )
            
    def read_params_from_panel( self ):  # scan panel parameters
        
        weightfile = self.t_weightfile.GetValue().strip()
        if not os.path.isfile( weightfile ):
            eprint( 'somclass: read_params_from_panel:' )
            eprint( '          file cannot be found:', weightfile )
            eprint( '          ...returning' )
            return False

        '''
        nclasses = int( self.t_nclasses.GetValue().strip() )
        if nclasses <= 0:
            eprint( 'somclass: read_params_from_panel:' )
            eprint( '          nclasses must be > 0' )
            eprint( '          ...returning' )
            return False
        '''
        self.p.weightfile = weightfile
        
        if self.c_apply_on_file_drop.GetValue():
            self.p.apply_on_file_drop = True
        else:
            self.p.apply_on_file_drop = False

        if self.c_stretch.GetValue():
            self.p.stretch = True
        else:
            self.p.stretch = False

        return True

    def write_params_to_panel( self ):   # write parameters to panel
        
        self.t_weightfile.SetValue( self.p.weightfile )
        #self.t_nclasses.SetValue( str( self.p.nclasses ) )
        self.c_apply_on_file_drop.SetValue( self.p.apply_on_file_drop )
        self.c_stretch.SetValue( self.p.stretch )

    # initialize graphics
    def init_panel( self, benchtop ):
        
        op_panel.init_panel( self, benchtop ) # start with basics
        
        v_sizer = wx.BoxSizer( wx.VERTICAL )
        v_sizer.Add( (1,10) ) # go down a bit on panel

        # for check boxes
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )

        self.c_apply_on_file_drop = wx.CheckBox( self.p_client, -1,
                                                 'apply on file drop' )
        self.c_apply_on_file_drop.SetToolTip( 'immediate execution when file is dropped or double clicking the data file in data suites' )

        self.c_apply_on_file_drop.Bind( wx.EVT_LEFT_UP, self.on_drop_click )

        h_sizer.Add( self.c_apply_on_file_drop )
        self.c_stretch = wx.CheckBox( self.p_client, -1,
                                      'stretch out class grey levels' )
        h_sizer.Add( self.c_stretch )
        v_sizer.Add( h_sizer )
        v_sizer.Add( (1,5) )  # add space

        '''
        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        l_prompt = wx.StaticText( self.p_client, -1,
                                  ' enter number of classes to use (0 for all): ' )
        h_sizer.Add( l_prompt, 0, wx.TOP, 5 )
        '''
        
        '''
        self.t_nclasses = wx.TextCtrl( self.p_client, -1, '',
                                       size=(35,25), style=wx.ALIGN_RIGHT )
        self.t_nclasses.SetToolTip( 'Weight file lists classes in descending order of frequency. For example, if you enter 5, then the 5 most frequent classes will be read and used.' )

        h_sizer.Add( self.t_nclasses, 0, wx.TOP )
        v_sizer.Add( h_sizer )
        '''
        v_sizer.Add( (1,15) )

        h_sizer = wx.BoxSizer( wx.HORIZONTAL )
        prompt = wx.StaticText( self.p_client, -1, 'enter weight filename:' )
        h_sizer.Add( prompt, 0, wx.TOP, 5 )

        self.t_weightfile = wx.TextCtrl( self.p_client, -1 ) 
        self.t_weightfile.SetToolTip( '  enter filename to read weights from' )
        dt = FileDrop( self.t_weightfile, self )
        self.t_weightfile.SetDropTarget( dt )
        h_sizer.Add( self.t_weightfile, 1, wx.EXPAND )
        
        # browse directory button
        b_browse = wx.Button( self.p_client, -1, 'browse', 
                              (232,79), (60,25) )
        b_browse.Bind( wx.EVT_LEFT_UP, self.on_browse )             
        b_browse.SetToolTip( 'browse directory for som classes file' )
        
        h_sizer.Add( b_browse, 0, wx.TOP )

        v_sizer.Add( h_sizer, 1, wx.EXPAND )
        self.p_client.SetSizer( v_sizer )
        self.write_params_to_panel()

    def on_drop_click( self, event ):
        
        if self.c_apply_on_file_drop.GetValue():
            self.p.apply_on_file_drop = False
            
        else:
            self.p.apply_on_file_drop = True

    # respond to file browse click
    def on_browse( self, event ):
        
        dlg = wx.FileDialog( self, "Choose a som classes file to read", 
                             os.getcwd(), "", "*", wx.FD_OPEN )

        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath().strip()
            self.t_weightfile.SetValue( path ) # update filename to gui

        dlg.Destroy()

    ############################################################
    # command line options
    ############################################################

    def usage( self ):
        
        eprint( '\nusage: somclass.py' )
        eprint( '       -h, --help' )
        eprint( '       -s, --stretch ' )
        eprint( '       -f weightfile, --file=weightfile' )
        eprint( '       -p param_file, --params=param_file' )
        eprint( 'param file overrides line arguments' ) 
        eprint( 'input is stdin, output is stdout' )

    def set_params( self, argv ):
        params = None

        try:                                
            opts, args = getopt.getopt( argv, 
                                        'hsp:f:', 
                                        ['help','stretch',
                                         'param=','file=' ] )
        except getopt.GetoptError as e:
            eprint( 'somclass: ' + str(e) )   
            self.usage()                          
            sys.exit( 2 )  
                   
        for opt, arg in opts:
            
            if opt in ( '-h', '--help' ):      
                self.usage()                     
                sys.exit( 0 )                
                
            elif opt in ( '-f', '--file' ):
                
                if not os.path.isfile( arg ):
                    eprint( 'somclass: weight file:', arg,
                            ' not found ...exiting')
                    sys.exit( 2 )
                self.p.weightfile = arg
                
            elif opt in ('-s','--stretch' ):
                self.p.stretch = True
                
            elif opt in ('-p', '--params'):
                
                if not os.path.ispath( arg ):
                    eprint( 'somclass: parameter file:', arg,
                            ' not found ...exiting')
                params = arg

        if params == None and self.p.weightfile == '':
            
            eprint( 'img_src: set_params: no weight filename given' )
            self.usage()
            sys.exit( 2 )

        if params != None :
            ok = self.read_params_from_file( params )
            if not ok:
                eprint( "somclass: cannot read parameter file" )
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
