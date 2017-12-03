#!/usr/bin/python

__doc__ = """

This file creates a directory for the client, initializes the required
DIBS stuff in that directory, stores some files, probes the stored
files, and checks if the probed files were probed correctly.

"""

import os, os.path, time, commands, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *


os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_ap_probe_client'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_ap_probe_server/dot_dibs'

RedirectOutputIfDesired('ap_probe_client')

SetupDefaultEnvs()

FILE_TO_STORE=testUtilsTestFiles[0]
FILE_TO_AUTOSTORE=testUtilsTestFiles[1]
AUTO_BACK_DIR=os.environ['DIBS_DIR'] + '/' + 'autoBackup'

DoCmd('\\rm -rf ${DIBS_DIR_BASE}')
os.mkdir(os.environ['DIBS_DIR_BASE'])

DoCmd(DIBS_PROG + ' add_peer --email ' + os.environ['DIBS_ADMIN'] +
      ' --peer ' + os.environ['DIBS_PEER'] + ' --local_quota 10000 --remote_quota 10000 --comment none --talk active --listen passive --host ${HOST} --port '
      + os.environ['DIBS_SERVER_PORT'])

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['daemonPort=' + os.environ['DIBS_CLIENT_PORT'],
                    'daemonTimeout = 15',
                    'pollInterval = 15'])

DoCmd(DIBS_PROG + ' store --name ' + FILE_TO_STORE)

DoCmd('ln -s ' + os.path.abspath(FILE_TO_AUTOSTORE) + ' ' + AUTO_BACK_DIR + 
      '/' + os.path.basename(FILE_TO_AUTOSTORE))

print 'Starting demon via spawn.\n'
os.spawnl(os.P_NOWAIT,DIBS_PROG,DIBS_PROG,'start_daemon')

time.sleep(5)
fd = open(os.environ['DIBS_DIR'] + '/stop_daemon','w')
fd.write('90\n')
fd.close()

time.sleep(45)

DoCmd(DIBS_PROG + ' probe --file ' + os.path.abspath(FILE_TO_STORE))
DoCmd(DIBS_PROG + ' probe --file ' +
      '/autoBackup/' + os.path.basename(FILE_TO_AUTOSTORE))

time.sleep(5)

DoCmd(DIBS_PROG + ' poll_passives')

time.sleep(5)

dir = os.environ['DIBS_DIR'] + '/incoming'
for file in os.listdir(dir):
    DoCmd(DIBS_PROG + ' process_message --file ' + dir + '/' + file)

ExpectEmpty(os.environ['DIBS_DIR'] + '/incoming')
ExpectEmpty(os.environ['DIBS_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/incoming')

DoCmd(DIBS_PROG + ' show_database --only stats | grep "GOOD_PROBES = 6L"')

print '\n'*4
print 'Test passed.'
print '\n'*4
print 'Asking server to stop.\n'

KeepTryingToStopDaemon(DIBS_PROG, os.environ['DIBS_SERVER_DIR'])


