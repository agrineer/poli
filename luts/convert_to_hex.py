#! /usr/bin/env python3

import os
import sys
from ezprint import eprint

infname = 'cetin.lut'
infile = open( infname, 'r' )

outfname = 'cetin.hex'
outfile = open( outfname, 'w' )

for l in infile:
    
    rgb = l.split(',')
    
    if not len(rgb) == 3:
        eprint( 'convert_to_hex: bad input file line read ... exiting' )
        sys.exit(1)

    rgb_values = [ int(rgb[0]), int(rgb[1]), int(rgb[2]) ]

    # strip '0x', pad to 2 digits
    hex_colors = [hex(value)[2:].zfill(2) for value in rgb_values]  
    hex_color_code = '#' + ''.join( hex_colors )
    
    outfile.write( hex_color_code + '\n' )
      
 
