
"""
The tests module contains various sub-modules for testing different
parts of DIBS.  The simplest way to run tests is to do

# cat echo import tests.all | python

"""

import sys, os, os.path

os.environ['DIBS_TEST_BASE'] = os.path.join(os.getcwd(),'tests')
os.environ['DIBS_EXE'] = os.path.join(os.getcwd(),'src','dibs_ui.py')

for item in ('DIBS_ADMIN','SMTP_SERVER',
             'DIBS_TESTING_KEY','DIBS_SECOND_TESTING_KEY'):
    if (not os.environ.has_key(item)):
        envVarUnset = ('Must set environment variable "'
                      + item + '" before testing.')
        raise Exception, envVarUnset
