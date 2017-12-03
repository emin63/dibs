#!/usr/bin/python

__doc__ = """

This file implements the client part of the aa_probe test which tests
the probe command with an active client and active server.

This file is meant to be called via 'gmake aa_probe'.
"""

import os, os.path, time, commands, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *

RedirectOutputIfDesired('aa_probe_client')

os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_aa_probe_client'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_aa_probe_server/dot_dibs'

SetupDefaultEnvs()

FILE_TO_STORE=testUtilsTestFiles[0]

DoCmd('\\rm -rf ${DIBS_DIR_BASE}')
os.mkdir(os.environ['DIBS_DIR_BASE'])

DoCmd(DIBS_PROG + ' add_peer --email ' + os.environ['DIBS_ADMIN'] +
      ' --peer ' + os.environ['DIBS_PEER'] + ' --local_quota 10000 --remote_quota 10000 --comment none --talk active --listen active --host ${HOST} --port '
      + os.environ['DIBS_SERVER_PORT'])

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['daemonPort=' + os.environ['DIBS_CLIENT_PORT'],
                    'daemonTimeout=15',
                    'pollInterval = 15'])

DoCmd(DIBS_PROG + ' store --name ' + FILE_TO_STORE)

print 'Starting demon via spawn.\n'
os.spawnl(os.P_NOWAIT,DIBS_PROG,DIBS_PROG,'start_daemon')

time.sleep(2)

DoCmd(DIBS_PROG + ' probe --file ' + os.path.abspath(FILE_TO_STORE))

time.sleep(30)  # this should be long enough for the probe to complete

dir = os.environ['DIBS_DIR'] + '/incoming'
for file in os.listdir(dir):
    DoCmd(DIBS_PROG + ' process_message --file ' + dir + '/' + file)

ExpectEmpty(os.environ['DIBS_DIR'] + '/incoming')
ExpectEmpty(os.environ['DIBS_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/incoming')

KeepTryingToStopDaemon(DIBS_PROG)

DoCmd(DIBS_PROG + ' show_database --only stats | grep "GOOD_PROBES = 3L"')

print '\n'*4
print 'Test passed.'
print '\n'*4
print 'Asking server to stop.\n'

KeepTryingToStopDaemon(DIBS_PROG, os.environ['DIBS_SERVER_DIR'])
