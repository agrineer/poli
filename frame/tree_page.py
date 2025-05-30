'''
@file tree_page.py
@author Scott L. Williams.
@package POLI
@section LICENSE

#  Copyright (C) 2010-2025 Scott L. Williams.

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

@section DESCRIPTION
Configure tree pages (operators and images)
'''

tree_page_copyright = 'Copyright (c) 2010-2025 Scott L. Williams, released under GNU GPL V3.0'

import os
import wx
import sys
import requests
from palette import palette
from bs4 import BeautifulSoup

# parse out html code for URL directory listing
# it used be that urllib would just list the directory files
# but it no longer exists
def parse_names( html ):
    
    soup = BeautifulSoup( html,'html.parser' )
    names = []
    for a in soup.find_all('a'):
        try:
            href = a['href']
            if href.find('?') != -1:
                pass
            else:
                if href[-1] == '/':     # directories have a trailing '/'
                    href = href[:-1]
                names.append( href )
        except KeyError:
            print( 'tree_page: parse_names: cannot parse names')
            return None
    
    names = names[1:]    # remove parent directory name
    return names

# insert a node into a tree
def put_node( page, ndir, path ):
    
    node_name = os.path.basename( path )

    item = page.add_tree_node( ndir, node_name, "item" )
    page.tree.SetItemData( item, path )   # associate pathname with icon

def populate_tree( page, paths ):

    # itemize path strings
    paths = paths.split(',')
 
    for i in range( len(paths) ):
        
        paths[i] = paths[i].strip()               # remove white spaces
        if not os.path.isdir( paths[i] ):
            raise Exception( 'tree_page: populate_tree: path:', paths[i],
                             'is not a directory' )

        base = os.path.basename( paths[i] )      # set up dir node
        tdir = page.add_tree_node( page.root, base, 'dir' )
    
        for tfile in os.listdir( paths[i] ):     # read dir files
            name = paths[i] + '/' + tfile        # reconstruct full path
            put_node( page, tdir, name )

        page.tree.SortChildren( tdir )

def populate_url_tree( page, paths ):

    # itemize path string
    paths = paths.split(',')

    for i in range( len(paths) ):
        
        paths[i] = paths[i].strip()                # remove white spaces

        # get url directory and html info soup (messy html text)
        try:
            html = requests.get( paths[i] ).text
            
        except IOError as e:
            raise Exception( 'tree_page:populate_url_tree error: ', e )
 
        # set up tree directory node
        base = os.path.basename( paths[i] )
        tdir = page.add_tree_node( page.root, base, 'dir' )  

        names = parse_names( html )
        for n in names:
            name = paths[i] + '/' + n            # reconstruct full path
            put_node( page, tdir, name )
                
        page.tree.SortChildren( tdir )

# create a page for an image suite
def make_page( name, suite, notebook ):
    
    page = palette( notebook )                   # create a page for this suite
    notebook.AddPage( page, name  )
  
    # check if network image
    if suite[:4] == 'http':
        populate_url_tree( page, suite )
        
    else:       
        populate_tree( page, suite ) # using local
    
    return page.tree  # return for event usage

# construct the suite tree and populate
def add_suites( suites, notebook, messages, event_func ):        

    if suites == None:
        return
        
    for suite in suites:      # read the suites file
        
        name, locator = suite
        tree = make_page( name, locator, notebook )

        if tree != None:
            tree.Bind( wx.EVT_TREE_ITEM_ACTIVATED, event_func )        
    
            messages.append( '\tsuites locator:\t' +
                             locator + '\tnamed\t' + name + '\n' )
