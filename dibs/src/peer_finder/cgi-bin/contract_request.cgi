#!/usr/bin/python

import dibs_cgi
import dibs_lib.peer_finder.main

print 'Content-Type: text/html\n\n'
result = dibs_lib.peer_finder.main.ProcessContractRequest()
print result
