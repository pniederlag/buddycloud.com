#!/usr/bin/env python
# -*- coding: utf-8 -*- #
from __future__ import unicode_literals

AUTHOR = u'buddycloud team'
SITENAME = u'buddycloud'
SITEURL = ''

TIMEZONE = 'Europe/Berlin'

DEFAULT_LANG = u'en'

DIRECT_TEMPLATES = ['index', 'style-guide']

STATIC_PATHS = [ 'img', 'CNAME' ]

THEME = 'buddycloud-theme'

MD_EXTENSIONS = [ 'codehilite(css_class=highlight)', 'extra', 'mdext.togglable_tabs', 'mdext.sequence_diagrams' ]

import os, sys
sys.path.append(os.path.join(os.getcwd(), "jinjaext"))
from table_of_contents import TableOfContents as TOC

JINJA_FILTERS = {
		  'extract_toc_info' : TOC.extractTableOfContentsInfo,
		  'create_toc' : TOC.createTableOfContents,
		  'add_toc_hooks' : TOC.addTableOfContentsHooks
		}

GOOGLE_ANALYTICS = "UA-1075750-9"

# Uncomment following line if you want document-relative URLs when developing
#RELATIVE_URLS = True
