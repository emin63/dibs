#!/usr/bin/python

__doc__ = """
This file contains code for daemon test case 2 for the 'server'.
Client is in quotes because dibs is peer-to-peer not client-server.
However, for this test, the 'client' stores data on the 'server' but
not vice-versa.

This file creates a directory in /tmp, and uses it to initailize
a DIBS peer, and start the daemon.  As opposed to test case 1,
test case 2 does a more comprehensive test.  Some additional tests
include:

* Testing the edit_peer command
* Testing the forget command
* Testing communication on non-default port

Note it is up to the caller or the 'client' to tell the 'server'
to stop.
"""

import os, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *

RedirectOutputIfDesired('t2_server')

SetupDefaultEnvs()

os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_t2_server'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_t2_server/dot_dibs'

DoCmd('\\rm -rf ' + os.environ['DIBS_DIR_BASE'])
os.mkdir(os.environ['DIBS_DIR_BASE'])

DoCmd(DIBS_PROG + ' add_peer --email ${USER}@${HOST}.blah --peer ' +
      os.environ['DIBS_PEER'] + ' --local_quota 2 --remote_quota 1 --comment none --talk passive --listen passive')

DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --email ${USER}@${HOST} ')
DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --talk passive ')
DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --listen active ')
DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --local_quota 10000 ')
DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --remote_quota 10000 ')
DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --comment blah ')

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['daemonPort = ' + os.environ['DIBS_SERVER_PORT'],
                    'pollInterval = 60',
                    'daemonTimeout = 60'])
                    
DoCmd(DIBS_PROG + ' start_daemon')


