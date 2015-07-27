#!/usr/bin/env python
# Copyright (c) Foundation for Learning Equality.
# See LICENSE for details.

from __future__ import print_function
from __future__ import unicode_literals

import logging
import os
import sys

try:
    from gi.repository import Gtk
except ImportError:
    print(
        "Could not find GTK3, maybe you don't have it installed or you are "
        "running from a virtualenv."
    )
    sys.exit(1)


sys.path.insert(0, os.path.abspath(os.getcwd()))

# create logger with 'kalite_gtk'
logger = logging.getLogger('kalite_gtk')
logger.setLevel(logging.DEBUG)

os.environ.setdefault(
    'KALITE_HOME',
    os.path.expanduser(os.path.join('~', '.kalite'))
)

KALITE_HOME = os.environ['KALITE_HOME']

if not os.path.isdir(KALITE_HOME):
    os.mkdir(KALITE_HOME)

# create file handler which logs even debug messages
fh = logging.FileHandler(
    os.path.expanduser(
        os.path.join(KALITE_HOME, 'kalite_gtk.log')
    )
)

fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()

if '--debug' in sys.argv:
    ch.setLevel(logging.DEBUG)
else:
    ch.setLevel(logging.ERROR)

# create formatter and add it to the handlers
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)


from kalite_gtk.mainwindow import MainWindow


def main(args=None):
    __ = MainWindow()
    Gtk.main()

if __name__ == "__main__":
    main()
