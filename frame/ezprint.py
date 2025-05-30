#
# print utilities to reduce clutter and to flush output stream
import sys

def eprint( *args ):
    print( *args, file=sys.stderr, flush=True )

def oprint( *args ):
    print( *args, file=sys.stdout, flush=True )
