#!/usr/bin/env python
#
# Copyright 2001-2004 by Vinay Sajip. All Rights Reserved.
#
# Permission to use, copy, modify, and distribute this software and its
# documentation for any purpose and without fee is hereby granted,
# provided that the above copyright notice appear in all copies and that
# both that copyright notice and this permission notice appear in
# supporting documentation, and that the name of Vinay Sajip
# not be used in advertising or publicity pertaining to distribution
# of the software without specific, written prior permission.
# VINAY SAJIP DISCLAIMS ALL WARRANTIES WITH REGARD TO THIS SOFTWARE, INCLUDING
# ALL IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL
# VINAY SAJIP BE LIABLE FOR ANY SPECIAL, INDIRECT OR CONSEQUENTIAL DAMAGES OR
# ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER
# IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT
# OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
#
# This file is part of the Python logging distribution. See
# http://www.red-dove.com/python_logging.html
#
"""Test harness for the logging module. Run all tests.

Copyright (C) 2001-2002 Vinay Sajip. All Rights Reserved.
"""

import os, sys, string
import tempfile
import logging

from paste.script.util import logging_config

def message(s):
    sys.stdout.write("%s\n" % s)

#----------------------------------------------------------------------------
# Test 4
#----------------------------------------------------------------------------

# config0 is a standard configuration.
config0 = """
[loggers]
keys=root

[handlers]
keys=hand1

[formatters]
keys=form1

[logger_root]
level=NOTSET
handlers=hand1

[handler_hand1]
class=StreamHandler
level=NOTSET
formatter=form1
args=(sys.stdout,)

[formatter_form1]
format=%(levelname)s:%(name)s:%(message)s
datefmt=
"""

# config1 adds a little to the standard configuration.
config1 = """
[loggers]
keys=root,parser

[handlers]
keys=hand1, hand2

[formatters]
keys=form1, form2

[logger_root]
level=NOTSET
handlers=hand1,hand2

[logger_parser]
level=DEBUG
handlers=hand1
propagate=1
qualname=compiler.parser

[handler_hand1]
class=StreamHandler
level=NOTSET
formatter=form1
args=(sys.stdout,)

[handler_hand2]
class=StreamHandler
level=NOTSET
formatter=form2
args=(sys.stderr,)

[formatter_form1]
format=%(levelname)s:%(name)s:%(message)s
datefmt=

[formatter_form2]
format=:%(message)s
datefmt=
"""

# config2 has a subtle configuration error that should be reported
config2 = string.replace(config1, "sys.stdout", "sys.stbout")

# config3 has a less subtle configuration error
config3 = string.replace(
    config1, "formatter=form1", "formatter=misspelled_name")

# config4: support custom Handler classes
config4 = string.replace(
    config1, "class=StreamHandler", "class=logging.StreamHandler")

def test4():
    for i in range(5):
        conf = globals()['config%d' % i]
        sys.stdout.write('config%d: ' % i)
        loggerDict = logging.getLogger().manager.loggerDict
        logging._acquireLock()
        try:
            saved_handlers = logging._handlers.copy()
            if hasattr(logging, '_handlerList'):
                saved_handler_list = logging._handlerList[:]
            saved_loggers = loggerDict.copy()
        finally:
            logging._releaseLock()
        try:
            fn = tempfile.mktemp(".ini")
            f = open(fn, "w")
            f.write(conf)
            f.close()
            try:
                logging_config.fileConfig(fn)
                #call again to make sure cleanup is correct
                logging_config.fileConfig(fn)
            except:
                if i not in (2, 3):
                    raise
                t = sys.exc_info()[0]
                message(str(t) + ' (expected)')
            else:
                message('ok.')
            os.remove(fn)
        finally:
            logging._acquireLock()
            try:
                logging._handlers.clear()
                logging._handlers.update(saved_handlers)
                if hasattr(logging, '_handlerList'):
                    logging._handlerList[:] = saved_handler_list
                loggerDict = logging.getLogger().manager.loggerDict
                loggerDict.clear()
                loggerDict.update(saved_loggers)
            finally:
                logging._releaseLock()

#----------------------------------------------------------------------------
# Test 5
#----------------------------------------------------------------------------

test5_config = """
[loggers]
keys=root

[handlers]
keys=hand1

[formatters]
keys=form1

[logger_root]
level=NOTSET
handlers=hand1

[handler_hand1]
class=StreamHandler
level=NOTSET
formatter=form1
args=(sys.stdout,)

[formatter_form1]
#class=test.test_logging.FriendlyFormatter
class=test_logging_config.FriendlyFormatter
format=%(levelname)s:%(name)s:%(message)s
datefmt=
"""

class FriendlyFormatter (logging.Formatter):
    def formatException(self, ei):
        return "%s... Don't panic!" % str(ei[0])


def test5():
    loggerDict = logging.getLogger().manager.loggerDict
    logging._acquireLock()
    try:
        saved_handlers = logging._handlers.copy()
        if hasattr(logging, '_handlerList'):
            saved_handler_list = logging._handlerList[:]
        saved_loggers = loggerDict.copy()
    finally:
        logging._releaseLock()
    try:
        fn = tempfile.mktemp(".ini")
        f = open(fn, "w")
        f.write(test5_config)
        f.close()
        logging_config.fileConfig(fn)
        try:
            raise KeyError
        except KeyError:
            logging.exception("just testing")
        os.remove(fn)
        hdlr = logging.getLogger().handlers[0]
        logging.getLogger().handlers.remove(hdlr)
    finally:
        logging._acquireLock()
        try:
            logging._handlers.clear()
            logging._handlers.update(saved_handlers)
            if hasattr(logging, '_handlerList'):
                logging._handlerList[:] = saved_handler_list
            loggerDict = logging.getLogger().manager.loggerDict
            loggerDict.clear()
            loggerDict.update(saved_loggers)
        finally:
            logging._releaseLock()
