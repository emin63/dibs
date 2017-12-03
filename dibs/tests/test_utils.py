
import sys, os, os.path, time, commands, tempfile

defaultKey = os.environ['DIBS_TESTING_KEY']
defaultSecondKey = os.environ['DIBS_SECOND_TESTING_KEY']

DIBS_PROG=os.environ['DIBS_EXE']


dibsBaseDir = os.path.split(os.environ['DIBS_TEST_BASE'])[0]
testUtilsTestFiles = [os.path.join(dibsBaseDir,'LICENSE'),
                      os.path.join(dibsBaseDir,'CHANGELOG'),
                      os.path.join(dibsBaseDir,'README')]

def DoGenericTest(testName,subdir,testParams):
    """
    Do a generic test by redirecting output, starting various scripts
    waiting for scripts to finish and throwing an exception if any fail.

    testName:    Name of the test.
    subdir:      Sub-directory where the test lives.
    testParams:  List of tuples where each tuple is of the form
                 (sleepTime, scriptName)

    After waiting for sleepTime, output is redirected and
    scriptName is spawned.
    """
    print 'Doing Test ' + testName
    
    tmpDir = os.path.split(tempfile.mktemp())[0]

    pythonExe = sys.exec_prefix + '/bin/python'

    pids = []
    for item in testParams:
        time.sleep(item[0])
        os.environ['DIBS_REDIRECT'] = os.path.join(tmpDir,item[1]+'.output')
        pids.append(os.spawnl(os.P_NOWAIT,pythonExe,pythonExe,
                              os.path.join('tests',subdir,item[1])))
        sys.stdout.flush()

    status = range(len(pids))
    for i in range(len(pids)):
        print 'Waiting for pid ' + `pids[i]`
        status[i] = int(os.waitpid(pids[i],0)[1])

    if ([0]*len(pids) != status):
        msg = ('exit status values for scripts ' +
               `map(lambda item: item[1], testParams)` + ' = ' + `status`)
        raise Exception, msg
    else:
        print 'Test ' + testName + ' passed.'

def RedirectOutputIfDesired(id):
    if (os.environ.has_key('DIBS_REDIRECT')):
        file = os.environ['DIBS_REDIRECT']
        print 'Redirecting all output for ' + id + ' to file ' + file + '.'
        fd = open(file,'w')
        fd.close()
        fd = os.open(file,os.O_WRONLY)
        sys.stdout.flush()
        os.dup2(fd,1)
        os.dup2(fd,2)
#        sys.stdout.close()
#        sys.stderr.close()
#        os.close(1)
#        os.close(2)
#        sys.stdout = fd
#        sys.stderr = fd
        sys.stdout.flush()


def SetupDefaultEnvs():
    """
    Setup default environment variables needed for testing.

    DIBS_KEY_NAME     : Name of the key for this dibs instance.
    DIBS_PEER         : Name of peer to trade with.
    DIBS_CLIENT_PORT  : Port number client will use.
    DIBS_SERVER_PORT  : Name of port the server will use.

    """
    for pair in [
        ('DIBS_KEY_NAME',defaultKey),
        ('DIBS_PEER',defaultKey),
        ('DIBS_CLIENT_PORT','3993'),
        ('DIBS_SERVER_PORT','9339'),
        ('DIBS_SECOND_PEER',defaultSecondKey),
        ('DIBS_SECOND_SERVER_PORT','9833')]:
        if (not os.environ.has_key(pair[0])):
            os.environ[pair[0]] = pair[1]
    

def EmptyP(path):
    for item in os.listdir(path):
        if (os.path.isfile(path+'/'+item)):
            return 0
        elif (0 == EmptyP(path+'/'+item)):
            return 0
    return 1
            

def ExpectEmpty(path):
    if (not EmptyP(path)):
        raise 'Path "' + path  + '" not empty.'

def ExpectNotEmpty(path):
    if (EmptyP(path)):
        print 'Directory "' + path + '/' + '" empty.'
        raise 'Directory "' + path + '/' + '" empty.'

def DoCmdAndSaveOutputToFile(cmd,file):
    pipe = os.popen(cmd + ' 2>&1 > ' + file,'r')
    o = pipe.read()
    s = pipe.close()
    if (s):
        raise Exception, ('Command "' + cmd +
                          '" returned non-zero exit status ' + `s` +
                          '\nwith output ' + `o`)


def DoCmd(cmd):
    (s,o) = commands.getstatusoutput(cmd)
    print 'Executing command: ' + cmd
    print o
    if (s):
        raise Exception, ('Command "' + cmd +
                          '" returned non-zero exit status ' + `s` + '.')
    else:
        return o

def AddOptionsToDIBSRC(rcFileName,optionList):
    fd = open(rcFileName,'a')
    for item in optionList:
        fd.write(item + '\n')
    fd.close()

def AddDefaultsToDIBSRC(rcFileName):
    AddOptionsToDIBSRC(rcFileName,[
        'logLevel = -50',
        'printLogLevel = -50',        
        'dibsAdmin = ' + `os.environ['DIBS_ADMIN']`,
        'smtpServer = ' + `os.environ['SMTP_SERVER']`,
        'dibsPublicKey = ' + '\'' +
        os.environ['DIBS_KEY_NAME'] + '\'',
        'dibsPrivateKey = ' + '\'' +
        os.environ['DIBS_KEY_NAME'] + '\'',
        'mailUserOnRecovery = 0'])

def StopDaemon(DIBS_PROG,dibsDir=None):
    oldDibsDir = os.environ['DIBS_DIR']    
    if (None != dibsDir):
        os.environ['DIBS_DIR'] = dibsDir

    DoCmd(DIBS_PROG + ' stop_daemon')
    os.environ['DIBS_DIR'] = oldDibsDir

def WaitForDaemonToStop(dibsDir=None):
    if (None == dibsDir):
        dibsDir = os.environ['DIBS_DIR']
    while(os.path.exists(dibsDir+'/stop_daemon')):
        print 'Trying to stop daemon: ' + dibsDir
        time.sleep(9)

def KeepTryingToStopDaemon(DIBS_PROG,dibsDir=None):
    StopDaemon(DIBS_PROG,dibsDir)
    WaitForDaemonToStop(dibsDir)
