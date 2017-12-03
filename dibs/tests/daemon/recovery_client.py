#!/usr/bin/python

__doc__ = """
This testcase verifies that recovery works properly.

This file creates a directory for the client, initializes the required
DIBS stuff in that directory, stores some files with two peers,
recovers the stored files using the recover_all command, and
checks if the stored files were recovered correctly.

"""

import os, os.path, time, commands, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *


os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_recovery_client'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_recovery_server/dot_dibs'
os.environ['DIBS_SECOND_SERVER_DIR'] = '/tmp/dibs_tests_recovery_second_server/dot_dibs'

RedirectOutputIfDesired('recovery_client')

SetupDefaultEnvs()

FILE_TO_STORE=testUtilsTestFiles[0]
FILE_TO_AUTOSTORE=testUtilsTestFiles[1]
AUTO_BACK_DIR=os.environ['DIBS_DIR'] + '/' + 'autoBackup'

DoCmd('\\rm -rf ${DIBS_DIR_BASE}')
os.mkdir(os.environ['DIBS_DIR_BASE'])

DoCmd(DIBS_PROG + ' show_database')
AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['daemonPort=' + os.environ['DIBS_CLIENT_PORT'],
                    'daemonTimeout = 15',
                    'pollInterval = 15'])

DoCmd(DIBS_PROG + ' add_peer --email ' + os.environ['DIBS_ADMIN'] +
      ' --peer ' + os.environ['DIBS_PEER'] + ' --local_quota 10000 --remote_quota 10000 --comment none --talk active --listen passive --host ${HOST} --port '
      + os.environ['DIBS_SERVER_PORT'])

DoCmd(DIBS_PROG + ' add_peer --email ' + os.environ['DIBS_ADMIN'] +
      ' --peer ' + os.environ['DIBS_SECOND_PEER'] + ' --local_quota 1000 --remote_quota 1000 --comment none --talk active --listen passive --host ${HOST} --port ' + os.environ['DIBS_SECOND_SERVER_PORT'])


DoCmd(DIBS_PROG + ' store --name ' + FILE_TO_STORE)

DoCmd('ln -s ' + os.path.abspath(FILE_TO_AUTOSTORE) + ' ' + AUTO_BACK_DIR + 
      '/' + os.path.basename(FILE_TO_AUTOSTORE))

print 'Starting demon via spawn.\n'
os.spawnl(os.P_NOWAIT,DIBS_PROG,DIBS_PROG,'start_daemon')

time.sleep(45)

# Make sure that files were distributed to both server and second_server
ExpectNotEmpty(os.environ['DIBS_SERVER_DIR'] + '/' + os.environ['DIBS_PEER'])
ExpectNotEmpty(os.environ['DIBS_SECOND_SERVER_DIR'] +
               '/' + os.environ['DIBS_PEER'])

print 'Trying to stop demon.\n'
KeepTryingToStopDaemon(DIBS_PROG)
print 'Demon stopped; trying to do recover.\n'

DoCmd(DIBS_PROG + ' recover_file --file ' + os.path.abspath(FILE_TO_STORE))
DoCmd(DIBS_PROG + ' recover_file --file ' +
      '/autoBackup/' + os.path.basename(FILE_TO_AUTOSTORE))

time.sleep(5)

DoCmd(DIBS_PROG + ' poll_passives')

time.sleep(5)

dir = os.environ['DIBS_DIR'] + '/incoming'
for file in os.listdir(dir):
    DoCmd(DIBS_PROG + ' process_message --file ' + dir + '/' + file)

DoCmd('diff ' + FILE_TO_STORE + ' ' + os.environ['DIBS_DIR'] + '/' +
      'recovery' + '/' + os.path.abspath(FILE_TO_STORE))

DoCmd('diff ' + FILE_TO_AUTOSTORE + ' ' +
      os.environ['DIBS_DIR'] + '/' +
      'recovery/' + 'autoBackup/' +
      os.path.basename(FILE_TO_AUTOSTORE))

time.sleep(5)

ExpectEmpty(os.environ['DIBS_DIR'] + '/incoming')
ExpectEmpty(os.environ['DIBS_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/incoming')

print '*'*20
print '\n'*4
print 'Erasing a bunch of stuff'
for item in ['dibs_database.fileDatabase','dibs_database.recoveryDatabase',
             'dibs_database.sortedPeerList','*.pyc',
             'dibs_database.peersRespondingToRecoverAll',
             'logfile','daemonLog','recovery',
             'autoBackup','*@*','incoming','outgoing','errorDir']:
    DoCmd('\\rm -rf ' + os.environ['DIBS_DIR'] + '/' + item)
print '*'*20
print '\n'*4

DoCmd('echo "DIBS_DIR contains :"; ls ' + os.environ['DIBS_DIR'])

DoCmd(DIBS_PROG + ' recover_all')

time.sleep(5)

DoCmd(DIBS_PROG + ' poll_passives')

DoCmd(DIBS_PROG + ' process_message')

DoCmd('diff ' + FILE_TO_STORE + ' ' + os.environ['DIBS_DIR'] + '/' +
      'recovery' + '/' + os.path.abspath(FILE_TO_STORE))

DoCmd('diff ' + FILE_TO_AUTOSTORE + ' ' +
      os.environ['DIBS_DIR'] + '/' +
      'recovery/' + 'autoBackup/' +
      os.path.basename(FILE_TO_AUTOSTORE))

print '\n'*4
print 'Test passed.'
print '\n'*4
print 'Asking server to stop.\n'

KeepTryingToStopDaemon(DIBS_PROG, os.environ['DIBS_SERVER_DIR'])

print '\n'*4
print 'Asking second server to stop.\n'

KeepTryingToStopDaemon(DIBS_PROG, os.environ['DIBS_SECOND_SERVER_DIR'])




