#!/usr/bin/python

import dibs_cgi
from dibs_lib.peer_finder import main

print 'Content-Type: text/html\n'
print main.ShowContracts()
print main.ContractServerInfoString()

