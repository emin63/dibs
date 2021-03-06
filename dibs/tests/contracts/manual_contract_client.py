#!/usr/bin/python

__doc__ = """

This file implements the client part of the manual_contract test which tests
the post_contract command and also tries to store some files.

Note that this test should send an email when the contract is succesfully
agreed upon.  Don't freak out.
"""

import os, os.path, time, commands, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *

RedirectOutputIfDesired('manual_contract_client')

os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_manual_contract_client'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_manual_contract_server/dot_dibs'

SetupDefaultEnvs()

contractName = 'test_contract'

DoCmd('\\rm -rf ${DIBS_DIR_BASE}')
os.mkdir(os.environ['DIBS_DIR_BASE'])
DoCmd(DIBS_PROG + ' show_database')

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['daemonPort=' + os.environ['DIBS_CLIENT_PORT'],
                    'daemonTimeout=15',
                    'pollInterval = 15'])

DoCmd(DIBS_PROG + ' propose_contract --url none --local_quota 10M --remote_quota 23M --talk active --listen active --host 127.0.0.1 --peer ' +
      os.environ['DIBS_PEER'] + ' --peer_host 127.0.0.1 --peer_port ' + os.environ['DIBS_SERVER_PORT'] + ' --peer_email ' + os.environ['DIBS_ADMIN'] +
      ' --contract_name ' + contractName)


print 'Starting demon via spawn.\n'
os.spawnl(os.P_NOWAIT,DIBS_PROG,DIBS_PROG,'start_daemon')

time.sleep(50)  

dir = os.environ['DIBS_DIR'] + '/incoming'
for file in os.listdir(dir):
    DoCmd(DIBS_PROG + ' process_message --file ' + dir + '/' + file)

ExpectEmpty(os.environ['DIBS_DIR'] + '/incoming')
ExpectEmpty(os.environ['DIBS_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/outgoing')
ExpectEmpty(os.environ['DIBS_SERVER_DIR'] + '/incoming')

StopDaemon(DIBS_PROG)
StopDaemon(DIBS_PROG,os.environ['DIBS_SERVER_DIR'])

DoCmd(DIBS_PROG + ' show_database --only peers | grep remoteQuota=10000000')
DoCmd(DIBS_PROG + ' show_database --only peers | grep localQuota=23000000')
DoCmd(DIBS_PROG + ' show_database --only proposed_contracts | grep "<PROPOSED_CONTRACT_DB></PROPOSED_CONTRACT_DB>"')

WaitForDaemonToStop()

print '\n'*4
print 'Test passed.'
print '\n'*4
print 'Asking server to stop.\n'

WaitForDaemonToStop(os.environ['DIBS_SERVER_DIR'])


