#!/usr/lib/ckan/default/bin/python
# EASY-INSTALL-ENTRY-SCRIPT: 'PasteScript==2.0.2','console_scripts','paster'
__requires__ = 'PasteScript==2.0.2'
import sys
from pkg_resources import load_entry_point

if __name__ == '__main__':
    sys.exit(
        load_entry_point('PasteScript==2.0.2', 'console_scripts', 'paster')()
    )