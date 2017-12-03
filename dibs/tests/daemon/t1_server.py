#!/usr/bin/python


__doc__ = """
This file contains code for daemon test case 1 for the 'server'.
Client is in quotes because dibs is peer-to-peer not client-server.
However, for this test, the 'client' stores data on the 'server' but
not vice-versa.

This file creates a directory in /tmp, and uses it to initailize
a DIBS peer, and start the daemon.

Note it is up to the caller or the 'client' to tell the 'server'
to stop.
"""

import os, sys

sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *

RedirectOutputIfDesired('t1_server')

SetupDefaultEnvs()

os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_t1_server'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_t1_server/dot_dibs'

DIBS_PROG=os.environ['DIBS_EXE']


DoCmd('\\rm -rf ' + os.environ['DIBS_DIR_BASE'])
os.mkdir(os.environ['DIBS_DIR_BASE'])

DoCmd(DIBS_PROG + ' add_peer --email ${USER}@${HOST} --peer ' +
      os.environ['DIBS_PEER'] + ' --local_quota 10000 --remote_quota 10000 --comment none --talk passive --listen active')

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['pollInterval = 60','daemonTimeout = 15',
                    'daemonPort=' + os.environ['DIBS_SERVER_PORT']])

DoCmd(DIBS_PROG + ' start_daemon')


