#!/usr/bin/python

__doc__ = """
This file contains code for daemon test case 2 for the 'client'.
Client is in quotes because dibs is peer-to-peer not client-server.
However, for this test, the 'client' stores data on the 'server' but
not vice-versa.

This file is meant to be called via 'make t2'.

This file creates a directory for the client, initializes the required
DIBS stuff in that directory, stores some files, recovers the stored
files, and checks if the stored files were recovered correctly.  This
test is more comprehensive than test cast 1 since it does things like

* Testing the edit_peer command
* Testing communication on non-default port
* Testing files with spaces in the file name

"""

import os,  os.path,  time,  commands,  shutil, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *

RedirectOutputIfDesired('t2_client')

os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_t2_client'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_t2_server/dot_dibs'

SetupDefaultEnvs()

shutil.copy(testUtilsTestFiles[0],'/tmp/FILE W SPACE IN NAME')

FILES_TO_STORE=[testUtilsTestFiles[0],'/tmp/FILE W SPACE IN NAME']
FILE_TO_AUTOSTORE=testUtilsTestFiles[1]
AUTO_BACK_DIR=os.environ['DIBS_DIR'] + '/' + 'autoBackup'

DoCmd('\\rm -rf ${DIBS_DIR_BASE}')
os.mkdir(os.environ['DIBS_DIR_BASE'])

DoCmd(DIBS_PROG + ' add_peer --email ${USER}@${HOST} --peer ' +
      os.environ['DIBS_PEER'] + ' --local_quota 3 --remote_quota 4 --comment none --talk active --listen passive --host ${HOST}')

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['daemonPort = ' + os.environ['DIBS_CLIENT_PORT'],
                    'daemonTimeout = 15',
                    'pollInterval = 15'])

DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --port ' + os.environ['DIBS_SERVER_PORT'])
DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --local_quota 10m ')
DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --remote_quota 10000 ')
DoCmd(DIBS_PROG + ' edit_peer --peer ' + os.environ['DIBS_PEER']
      + ' --comment blah ')

for file in FILES_TO_STORE:
    DoCmd(DIBS_PROG + ' store --name ' + `file`)

DoCmd('ln -s ' + os.path.abspath(FILE_TO_AUTOSTORE) + ' ' + AUTO_BACK_DIR + 
      '/' + os.path.basename(FILE_TO_AUTOSTORE))

print 'Starting demon via spawn.\n'
os.spawnl(os.P_NOWAIT,DIBS_PROG,DIBS_PROG,'start_daemon')

time.sleep(5)

fd = open(os.environ['DIBS_DIR'] + '/stop_daemon','w')
fd.write('90\n')
fd.close()

time.sleep(45)

for file in FILES_TO_STORE:
    DoCmd(DIBS_PROG + ' recover_file --file ' + `os.path.abspath(file)`)

DoCmd(DIBS_PROG + ' recover_file --file ' +
      '/autoBackup/' + os.path.basename(FILE_TO_AUTOSTORE))

time.sleep(5)

DoCmd(DIBS_PROG + ' poll_passives')

time.sleep(5)

dir = os.environ['DIBS_DIR'] + '/incoming'
for file in os.listdir(dir):
    DoCmd(DIBS_PROG + ' process_message --file ' + dir + '/' + file)

for file in FILES_TO_STORE:
    DoCmd('diff "' + file + '" "' + os.environ['DIBS_DIR'] + '/' +
          'recovery' + '/' + os.path.abspath(file) + '"')

DoCmd('diff ' + FILE_TO_AUTOSTORE + ' ' +
      os.environ['DIBS_DIR'] + '/' +
      'recovery' + '/autoBackup/' +
      os.path.basename(FILE_TO_AUTOSTORE))

time.sleep(5)

ExpectEmpty(os.environ['DIBS_DIR'] + '/incoming')
ExpectEmpty(os.environ['DIBS_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/incoming')

print '\n'*4
print 'Test passed.'
print '\n'*4
print 'Asking server to stop.\n'

KeepTryingToStopDaemon(DIBS_PROG, os.environ['DIBS_SERVER_DIR'])




