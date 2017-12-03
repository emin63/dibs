#!/usr/bin/python

import cgi
import cgitb; cgitb.enable() # put error messages into httpd error log

import dibs_cgi
from dibs_lib.peer_finder import main

print "Content-Type: text/html"     # HTML is following
print                               # blank line, end of headers

print main.ShowContractServerUsage()
