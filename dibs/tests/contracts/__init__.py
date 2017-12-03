
import os, os.path, sys
sys.path.append(os.environ['DIBS_TEST_BASE'])
import test_utils

parametersForTests = {'manual_contract':[(3,'manual_contract_server.py'),
                                       (3,'manual_contract_client.py')],
                      'post_contract':[(3,'post_contract_server.py'),
                                       (3,'post_contract_client.py')]}


def DoTest(name):
    if ('all'==name):
        keys = parametersForTests.keys()
        keys.sort()
        for t in keys:
            test_utils.DoGenericTest(t,'contracts',parametersForTests[t])
    elif (parametersForTests.keys().count(name)):
        test_utils.DoGenericTest(name,'contracts',parametersForTests[name])
    else:
        raise Exception, 'No test named ' + `name` + ' exists.\n'
    
