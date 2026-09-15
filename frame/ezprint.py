#
# print utilities to reduce clutter and to flush output stream
import sys

# print to stderr with new line
def eprint( *args ):
    print( *args, file=sys.stderr, flush=True )

# print to stderr without new line (stop)
def eprints( *args ):
    print( *args, file=sys.stderr, flush=True, end='' )

# print to sdtout with new line
def oprint( *args ):
    print( *args, file=sys.stdout, flush=True )
