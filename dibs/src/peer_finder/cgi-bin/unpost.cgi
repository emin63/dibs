#!/usr/bin/python

import dibs_cgi
import dibs_lib.peer_finder.main

print 'Content-Type: text/html\n'
print dibs_lib.peer_finder.main.ProcessRevokeRequest()
