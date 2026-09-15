#! /usr/bin/env python3

'''
@file cetin_batch.py
@author Scott L. Williams.
@package POLI
@brief POLI batch implementation of cetin SOM
@LICENSE
# 
#  Copyright (C) 2020-2025 Scott L. Williams.
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

# an example of using POLI 'batch' mode

cetin_batch_copyright = 'cetin_batch.py Copyright (c) 2020-2025 Scott L. Williams, released under GNU GPL V3.0'

import os
import sys
import glob
import tempfile
import numpy as np

from norm import norm
from msom import msom
from render import render
from ezprint import eprint
from cetin_src import cetin_src


# instantiate the operators
src = cetin_src.cetin_src( 'cetin_src' )   # no parameters to tweak

# normalize operator
nrm = norm.norm( 'norm' )
nrm.p.ntype = 0                # 0 for 0 to 1; -1 for -1 to 1
nrm.p.write = False            # write coefficients?
nrm.p.filepath = 'ncoeffs.txt' # coefficient output file
nrm.p.skip = 0                 # interlace skip factor

# SOM operator
som = msom.msom( 'msom' )      # parameters below are only some available
som.p.shape = (4,4)            # nodal topology
som.p.sigma = 2.0              # spread of the neighborhood function
som.p.nepochs = 2              # number of full data set to sample
som.p.rate =  0.1              # initial learning rate 
som.p.init_weights = 'random'  # initiate training weights with random values
som.p.neighborhood_function = 'gaussian'

# render to file operator
rnd = render.render( 'render' )
rnd.p.filepath = './test.jpg'
rnd.p.RGB = False
rnd.p.greybuf = 0

POLI_HOME = os.environ['POLI_HOME']
rnd.p.lutfile = POLI_HOME + '/luts/halfbow.lut'

# ----------------------------------------------------------------------------

# main

if __name__ == '__main__':

    # declare numpy version
    eprint( 'cetin_batch: using numpy version', np.version.version )

    src.run()               # construct the cetin datacube

    nrm.source = src.sink   # link nrm source to src sink
    nrm.run()               # normalize the cetin datacube (not needed)

    som.source = nrm.sink  # link nrm sink to msom source
    som.run()              # classify (train) the data

    rnd.source = som.sink  # link msom sink to render source
    rnd.run()               # render the som labeled image to file

    eprint( 'cetin batch done' )
