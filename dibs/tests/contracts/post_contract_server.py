#!/usr/bin/python

__doc__ = """

This file implements the server part of the post_contract test which tests
the post_contract command.  The server posts the contract, the client
sends a proposal, the server responds, and the client processes the response.

"""

import os, os.path, time, commands, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
from test_utils import *

RedirectOutputIfDesired('post_contract_server')

os.environ['DIBS_DIR_BASE'] = '/tmp/dibs_tests_post_contract_server'
os.environ['DIBS_DIR'] = os.environ['DIBS_DIR_BASE'] + '/dot_dibs'
os.environ['DIBS_SERVER_DIR'] = '/tmp/dibs_tests_post_contract_server/dot_dibs'

SetupDefaultEnvs()

contractName = 'test_contract+' + os.environ['DIBS_ADMIN']

DoCmd('\\rm -rf ${DIBS_DIR_BASE}')
os.mkdir(os.environ['DIBS_DIR_BASE'])
DoCmd(DIBS_PROG + ' show_database')

AddDefaultsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py')
AddOptionsToDIBSRC(os.environ['DIBS_DIR'] + '/dibsrc.py',
                   ['daemonPort=' + os.environ['DIBS_SERVER_PORT'],
                    'daemonTimeout=15',
                    'defaultContractServerUrl="www.martinian.com:8000/~emin/cgi-bin"',
                    'pollInterval = 15'])

DoCmd(DIBS_PROG + ' post_contract --min_quota 10M --max_quota 30m --quota_mult 2.3 --lifetime 86400 --contract_name ' + contractName)

DoCmd(DIBS_PROG + ' show_database')

DoCmd(DIBS_PROG + ' start_daemon')

DoCmd(DIBS_PROG + ' show_database --only peers | grep localQuota=10000000')
DoCmd(DIBS_PROG + ' show_database --only peers | grep remoteQuota=23000000')

DoCmd(DIBS_PROG + ' show_database --only posted_contracts | grep "<POSTED_CONTRACT_DB></POSTED_CONTRACT_DB>"')
