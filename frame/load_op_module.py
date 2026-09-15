'''
@file load_op_module.py
@author Scott L. Williams.
@package POLI
@section LICENSE

#  Copyright (C) 2020-2025 Scott L. Williams.

#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
# 
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details. 
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#

@section DESCRIPTION
Keystone module for POLI; dynamically loads an operator module
'''

load_op_module_copyright = 'load_op_module.py Copyright (c) 2010-2025 Scott L. Williams released under GNU GPL V3.0'

import os
import sys
import zipimport
from ezprint import eprint

from urllib import request
from importlib.util import spec_from_file_location, module_from_spec

def try_loading( name, paths ):

     for path in paths:
        spec = spec_from_file_location( name, os.path.join(path, f'{name}.py'))
        if spec != None:
            # If a spec was found but the file is invalid,
            # let exceptions propagate
            module = module_from_spec( spec )
            spec.loader.exec_module( module )
            return module
        
        raise ModuleNotFoundError

def cleanup( name_or_path, paths ):
    
    folder, filename = os.path.split(name_or_path)
    if not folder:
        # TODO: support for dotted package names?
        # Can that even be done if we have opted not to modify sys.path?
        return name_or_path, paths or sys.path
    
    if paths:
        raise ValueError("redundant path(s) specified")
    
    name, extension = os.path.splitext(filename)
    if extension != '.py':
        raise ValueError("directly specified file must be a .py file")
    return name, [folder]


def dynamic_import( name_or_path:str, *paths:str, use_cache:bool=False ):
    """
    Dynamically import the specified module from a Python source file,
    directly specifying where to find the file.
    name_or_path -> if it includes a path separator, this is a complete path
                    to the file including its name and extension; *paths must
                    not be provided. Otherwise, it is the name of the module
                    to search for; the filename will be inferred.
    *paths -> if a name was provided, these paths will be searched. Defaults
              to sys.path if a search is required and no paths are provided.
    use_cache -> if set, the name will be looked up in sys.modules before
                 attempting dynamic import, with that result used instead;
                 if dynamic import is attempted and successful, sys.modules
                 will be updated with the result.
                 this is the system module cache not the poli/.cache
    """
    
    name, paths = cleanup( name_or_path, paths )
    if use_cache:
        
        try:
            return sys.modules[ name ]
        except KeyError:
            pass # proceed with the actual dynamic import logic
        
    module = try_loading( name, paths )
    
    if use_cache:
        sys.modules[ name ] = module
        
    return module

# retrieve starting module for a zip package
def load_zip_module( package_path ):

    # parse package_path string to get ...
    module_name = os.path.basename( package_path )[:-4]
    package_name = module_name

    # import zip package first
    importer = zipimport.zipimporter( package_path )
    package = importer.load_module( module_name )

    # import principal module
    return  importer.load_module( package_name + '/' + module_name )

# retrieve starting module for given package
def load_operator( path ):

     opname = os.path.basename( path ) 

     # is this a URL module?
     if path[:4] == 'http':

          # URL modules are zipped, just as well for net communication
          if path[-4:] != '.zip':

               # TODO: need to post to messages
               eprint( 'load_operator: remote URL operator needs to be',
                      'a zip file' )
               return
               
          # get environment variables $POLI_HOME
          try:
               POLI_HOME = os.environ['POLI_HOME']
               
          except OSError as e:
               eprint( str(e) )
               return
                        
          cache_dir = POLI_HOME + '/.cache/'
          cache_path = cache_dir + opname
              
          # housekeeping
          if not os.path.isdir( cache_dir ):
               os.mkdir( cache_dir ) 

          # retrieve from URL 
          request.urlretrieve( path, cache_path )
          module = load_zip_module( cache_path )
          eprint( 'load_op_module: operator', opname,
                  'retrieved from', path )
          return module
   
     elif path[-4:] == '.zip':        # local zip file
          return load_zip_module( path )

     else:
          # use a local directory operator
          return dynamic_import( opname, path )
     
''' version with cache option
# retrieve starting module for given package
def load_operator( path ):

     opname = os.path.basename( path ) 

     # is this a URL module?
     if path[:4] == 'http':

          # URL modules are zipped, just as well for net communication
          if path[-4:] != '.zip':

               # TODO: need to post to messages
               eprint( 'load_operator: remote URL operator needs to be a zip file' )
               return
               
          # get environment variables $POLI_HOME, $POLI_USE_CACHE
          POLI_HOME = os.environ['POLI_HOME']
          POLI_USE_CACHE = os.environ['POLI_USE_CACHE']

          cache_dir = POLI_HOME + '/.cache/'
          cache_path = cache_dir + opname
          POLI_USE_CACHE = os.environ['POLI_USE_CACHE']
          use_cache = False
          if ( POLI_USE_CACHE in [ 'YES','Yes','Y','yes','y'] ):
               use_cache = True
               
          # housekeeping
          if not os.path.isdir( cache_dir ):
               if use_cache: 
                    eprint( 'load_operator: there is no cache directory:',
                            cache_dir, 'will make...' )
               # make cache directory anyway to stash operator if asked for
               # in later runs later
               os.mkdir( cache_dir ) 
 
          if use_cache:
                         
               try:
                    eprint( 'load_operator: looking for operator:', opname )
                    module = load_zip_module( cache_path )
                    eprint( ' operator found.' )
                    return module 
               except:
                    eprint( 'load_operator: there is no operator:', opname,
                            'in cache, will fetch...' )
 
                    # not there, get url operator directory and put in cache
                    request.urlretrieve( path, cache_path )
                    module = load_zip_module( cache_path )
                    eprint( ' operator', opname, ' retrieved.' )
                    return module
          else:
               eprint( 'load_operator: not using cache.' )
               eprint( 'load_operator: retrieving', opname,
                       ' from', path )
 
               # update operator in the cache
               request.urlretrieve( path, cache_path )
               module = load_zip_module( cache_path )
               return module
   
     elif path[-4:] == '.zip':        # local zip file
          return load_zip_module( path )

     else:
          # use a local directory operator
          return dynamic_import( opname, path )
'''
