#!python

# This is the main executable for dibs.
# All it does is import the dibs_ui.py from dibs_lib.
# The installer will put all the dibs python files
# in dibs_lib so that the import works.

import dibs_lib

import imp, sys

# The following two lines are required for pickle to work
# properly on windows.
sys.path.append(imp.find_module('dibs_lib')[1])
sys.path.append(imp.find_module('ffield')[1])


from dibs_lib.dibs_ui import *
