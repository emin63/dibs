import time
import traceback
import os, os.path

import dibs_options
from dibs_utils import *

LOG_DEBUG = -20
LOG_INFO = -10
LOG_WARNING = 0
LOG_ERROR = 10
LOG_CRITICAL = 20
LOG_ALWAYS = 10000

def RotateLogs(logFileName):
    for i in range(8,0,-1):
        if (os.path.exists(logFileName + '.' + `i`)):
            if (os.path.exists(logFileName + '.' + `i+1`)):
                os.remove(logFileName + '.' + `i+1`)
            os.rename(logFileName + '.' + `i`,logFileName + '.' + `i+1`)
    if (os.path.exists(logFileName + '.1')):
        os.remove(logFileName + '.1')
    os.rename(logFileName,logFileName + '.1')

class DIBSLogger:
    "A class to log dibs stuff."

    def __init__(self,logFile,logLevel=LOG_WARNING,printLogLevel=LOG_INFO):
        print 'opening log ' + logFile + ' at level ' + `logLevel`
        self.logLevel = logLevel
        self.printLogLevel = printLogLevel
        if (os.path.exists(logFile) and
            (os.path.getsize(logFile) > dibs_options.maxLogSize)):
            print 'Rotating logs'
            RotateLogs(logFile)
        self.fd = open(logFile,'a')
        curTime = time.asctime(time.localtime(time.time()))
        self.fd.write('DIBS logging started at ' + curTime +
                      ' (level ' + `logLevel` + ').\n')

    def __del__(self):

        # if __del__ is called after time has been unimported reimport time
        import time
        print 'closing log'
        self.fd.write('Closed log at ' + \
                      time.asctime(time.localtime(time.time())) + '.\n')
        self.fd.close()

    def Log(self,msg,level=LOG_INFO):
        if (level >= self.logLevel):
            curTime = time.asctime(time.localtime(time.time()))
            self.fd.write('[' + curTime + ']: ' + msg + '\n')

    def LogError(self,msg,level=LOG_ERROR):
        self.Log(msg,level)
        self.fd.flush()

    def CloseLog(self):
        curTime = time.asctime(time.localtime(time.time()))
        self.fd.write('DIBS closing log at ' + curTime + '.\n')
        self.fd.flush()
        self.fd.close()

    def PrintAndLog(self,msg,logLevel=LOG_INFO,printLevel=None):
        if (None==printLevel):
            printLevel = logLevel
            
        if (printLevel >= self.printLogLevel):
            print msg
            
        if (logLevel >= self.logLevel):
            self.Log(msg,logLevel)
            self.fd.flush()

Logger = DIBSLogger(dibs_options.logFile,
                    dibs_options.logLevel,dibs_options.printLogLevel)

