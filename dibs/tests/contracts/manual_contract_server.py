#!/usr/bin/python

__doc__ = """

This file implements the server part of the manual_contract test which
tests the post_contract command.  The server posts the contract, the
client sends a proposal, the server responds, and the client processes
the response.  The reason the test is called 'manual_contract' is
because neither the server nor the client uses the web site to
advertise/grab contract info.

"""

import os, os.path, time, commands, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *

RedirectOutputIfDesired('manual_contract_server')

os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_manual_contract_server'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_manual_contract_server/dot_dibs'

SetupDefaultEnvs()

contractName = 'test_contract'

DoCmd('\\rm -rf ${DIBS_DIR_BASE}')
os.mkdir(os.environ['DIBS_DIR_BASE'])
DoCmd(DIBS_PROG + ' show_database')

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['daemonPort=' + os.environ['DIBS_SERVER_PORT'],
                    'daemonTimeout=15',
                    'pollInterval = 15'])

DoCmd(DIBS_PROG + ' post_contract --min_quota 10M --max_quota 30m --quota_mult 2.3 --lifetime 86400 --contract_name ' + contractName + ' --url none')

DoCmd(DIBS_PROG + ' start_daemon')

DoCmd(DIBS_PROG + ' show_database --only peers | grep localQuota=10000000')
DoCmd(DIBS_PROG + ' show_database --only peers | grep remoteQuota=23000000')
DoCmd(DIBS_PROG + ' show_database --only posted_contracts | grep "<POSTED_CONTRACT_DB></POSTED_CONTRACT_DB>"')
