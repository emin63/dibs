#!/usr/bin/python

__doc__ = """
This file implements the server part of the aa_probe test which tests
the probe command with an active client and active server.

This file is meant to be called via 'gmake aa_probe'.
"""

import os, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *

RedirectOutputIfDesired('aa_probe_server')

SetupDefaultEnvs()

os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_aa_probe_server'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_aa_probe_server/dot_dibs'

DoCmd('\\rm -rf ' + os.environ['DIBS_DIR_BASE'])
os.mkdir(os.environ['DIBS_DIR_BASE'])

DoCmd(DIBS_PROG + ' add_peer --email ${USER}@${HOST} --peer ' +
      os.environ['DIBS_PEER'] + ' --local_quota 10000 --remote_quota 10000 --comment none --talk active --listen active --host ${HOST} --port ' + os.environ['DIBS_CLIENT_PORT'])

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['pollInterval = 30',
                    'daemonTimeout = 15',
                    'daemonPort=' + os.environ['DIBS_SERVER_PORT']])

DoCmd(DIBS_PROG + ' start_daemon')


