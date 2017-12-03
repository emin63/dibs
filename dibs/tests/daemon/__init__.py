

"""
The daemon module contains various scripts which mainly test the
daemon functionality by doing things like store, unstore, probe,
recover, etc.
"""

import os, os.path, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
import test_utils

parametersForTests = {'t1':[(0,'t1_server.py'),(2,'t1_client.py')],
                      't2':[(20,'t2_server.py'),(10,'t2_client.py')],
                      'test_recovery':[(5,'recovery_server.py'),
                                  (5,'recovery_second_server.py'),
                                  (5,'recovery_client.py')],
                      'ap_probe':[(3,'ap_probe_server.py'),
                                  (3,'ap_probe_client.py')],
                      'aa_probe':[(3,'aa_probe_server.py'),
                                  (3,'aa_probe_client.py')]}

def DoTest(name):
    if ('all'==name):
        keys = parametersForTests.keys()
        keys.sort()
        for t in keys:
            test_utils.DoGenericTest(t,'daemon',parametersForTests[t])
    elif (parametersForTests.keys().count(name)):
        test_utils.DoGenericTest(name,'daemon',parametersForTests[name])
    else:
        raise Exception, 'No test named ' + `name` + ' exists.\n'
    
