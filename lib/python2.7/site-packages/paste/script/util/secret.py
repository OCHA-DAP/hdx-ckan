# (c) 2005 Ian Bicking and contributors; written for Paste (http://pythonpaste.org)
# Licensed under the MIT license: http://www.opensource.org/licenses/mit-license.php
"""
Create random secrets.
"""

import os
import random

def random_bytes(length):
    """
    Return a string of the given length.  Uses ``os.urandom`` if it
    can, or just pseudo-random numbers otherwise.
    """
    try:
        return os.urandom(length)
    except AttributeError:
        return ''.join([
            chr(random.randrange(256)) for i in xrange(length)])

def secret_string(length=25):
    """
    Returns a random string of the given length.  The string
    is a base64-encoded version of a set of random bytes, truncated
    to the given length (and without any newlines).
    """
    s = random_bytes(length).encode('base64')
    for badchar in '\n\r=':
        s = s.replace(badchar, '')
    # We're wasting some characters here.  But random characters are
    # cheap ;)
    return s[:length]
