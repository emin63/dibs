import os
import os.path
import sys
import traceback

__doc__ = """
This file contains various options which the user can override using
the dibsrc.py file.  A detailed description of each option is
contained in the texinfo documentation.
"""

def SafeEnvGet(var,default,warn=1):
    """
    Get the environment variable var if it exists or set it to the
    value default and return default.  If the variable didn't exist
    then print a warning unless warn=0.
    """
    if (not os.environ.has_key(var)):
        if (warn):
            print ('WARNING: environment variable "' + var +
                   '" unset.  Using default value of "' + `default` + '".\n')
        os.environ[var] = default
    return os.environ[var]



def GetDIBS_DIR():
    "Figure out a directory to use for dibs data."
    if (os.environ.has_key('DIBS_DIR')):
        return os.environ['DIBS_DIR']
    elif (os.environ.has_key('HOME')):
        return os.path.join(os.environ['HOME'],'.dibs')
    elif (os.environ.has_key('USERPROFILE')):
        return os.path.join(os.environ['USERPROFILE'],'.dibs')
    else:
        raise ('Can\'t get DIBS_DIR: ' +
               'no DIBS_DIR, HOME, or USERPROFILE env vars.')
    
DIBS_DIR = GetDIBS_DIR()

dibsPublicKey = (SafeEnvGet('USER','unknown_user') + '.dibs' + '@' +
               SafeEnvGet('HOST','unknown_host'))
dibsPrivateKey = (SafeEnvGet('USER','unknown_user') + '.dibs' + '@' +
               SafeEnvGet('HOST','unknown_host'))

dibsAdmin = (SafeEnvGet('USER','unknown_user') + '@' +
             SafeEnvGet('HOST','unknown_host'))

smtpServer = 'localhost'

mailUserOnRecovery = 1

kbPerFile = 10 * 2**10
redundantPieces = 2

logFile = os.path.join(DIBS_DIR,'logfile')
maxLogSize = 1000000

gpgProg = 'gpg'

sleepTime = 10

errWarnCount = 30
errMaxCount = 60
errorDir = os.path.join(DIBS_DIR,'errorDir')

daemonLogFile = os.path.join(DIBS_DIR,'daemonLog')
daemonStopFile = os.path.join(DIBS_DIR,'stop_daemon')
daemonTimeout = 60*15
pollInterval = 3600
daemonPort = 6363

probeTimeout = 86400*1
probePeriod = 86400/2

sendMsgThreshold = 30

# How old a message can be in seconds before we complain about
# not being able to deliver it.
maxMsgAge = 86400 * 10 # 10 days

hostname = SafeEnvGet('HOST','localhost')

pythonExe = sys.executable
dibsExe = sys.argv[0]

autoBackupDir = os.path.join(DIBS_DIR,'autoBackup')

logLevel = 0
printLogLevel = -10

defaultContractServerURL = 'www.martinian.com:8000/~emin/cgi-bin/peer_finder'

if (os.name == 'nt' or os.name == 'dos'):
    rootDir = os.path.abspath('')[0:3]
else:
    rootDir = os.sep

# Currently, we don't list the following options
# in the documentation because the user probably shouldn't
# fiddle with them.  They are in here instead of dibs_constants
# because they need DIBS_DIR which gets set in here.
databaseFilePrefix = os.path.join(DIBS_DIR,'dibs_database')
lockfile = os.path.join(DIBS_DIR,'dibs_database' + '.lock')
recoveryDir = os.path.join(DIBS_DIR,'recovery')
outgoingQueueDir = os.path.join(DIBS_DIR,'outgoing')
incomingQueueDir = os.path.join(DIBS_DIR,'incoming')
statsMsgDir = os.path.join(DIBS_DIR,'statsDir')

rcFileRead = 0

if (os.path.exists(os.path.join(DIBS_DIR,'dibsrc.py'))):
    try:
        sys.path.append(DIBS_DIR)
        from dibsrc import *
        rcFileRead = 1
    except Exception, e:
        exc_info = sys.exc_info()
        print 'Warning: Unable to read '+`os.path.join(DIBS_DIR,'dibsrc.py')`
        print '         because of exception ' + e.__str__()
        print '         Traceback:'
        for line in traceback.format_tb(exc_info[2]):
            print line
         
