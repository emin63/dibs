#!/usr/bin/python

__doc__ = """
Test probe for active client and passive server.
"""

import os, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *


SetupDefaultEnvs()

RedirectOutputIfDesired('ap_probe_server')

os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_ap_probe_server'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_ap_probe_server/dot_dibs'

DoCmd('\\rm -rf ' + os.environ['DIBS_DIR_BASE'])
os.mkdir(os.environ['DIBS_DIR_BASE'])

DoCmd(DIBS_PROG + ' add_peer --email ${USER}@${HOST} --peer ' +
      os.environ['DIBS_PEER'] + ' --local_quota 10000 --remote_quota 10000 --comment none --talk passive --listen active')

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['pollInterval = 30','daemonTimeout = 30',
                    'daemonPort=' + os.environ['DIBS_SERVER_PORT']])

DoCmd(DIBS_PROG + ' start_daemon')


