

"""
This module implements DIBS daemon operations such as listening
for connections from peers on different machines.

TODO:
Currently, we only process a single connection at a time because
I don't know of a way to emulate fork that works on all platforms.
It would be nice to fix this.

Need a way to do automated testing of daemon stuff, but that
might be a little tricky with only one user account.  It might
work if we issue an add_peer command for ourselves.

Alternatively, you could have an interactive or adjustable testing
script which takes usernames and passwords as options.
"""

import time, socket, select, re, os, os.path, tempfile

import dibs_constants
import dibs_options
import dibs_statistics
import dibs_logger

from dibs_utils import *
from dibs_exceptions import *

sOK = 'OK' # string to send to acknowledge success

rOK = '(?P<ok>^ *OK *$)' #regexp for OK string
rOK = (rOK,re.compile(rOK) )

# regexp for OK or INCOMING_FILE command
rOKorI= ('(' + rOK[0] + '|' +
         '(?P<inc>^ *INCOMING_FILE +(?P<arg1>[0-9]+L?) *$))' )
rOKorI = (rOKorI,re.compile(rOKorI))

rCmd = '(^ *(?P<cmd>(HELO)|(HELLO)|(GET)|(GIVE)|(FINISHED))) *(?P<arg1>[^ ]+)* *$'
rCmd = (rCmd,re.compile(rCmd))

socketErrsToIgnore = (['Resource temporarily unavailable',
                       'Connection reset by peer',
                       'Connection refused','Broken Pipe',
                       'Operation timed out',
                       'The socket operation could not complete without blocking'])

class DIBSCommunicator:
               
    def SocketTransmit(self,data,pad=1):
        if (pad):
            data = string.ljust(data,dibs_constants.daemonCmdSize)
            assert len(data) <= dibs_constants.daemonCmdSize, (
                'Command "' + data + '" is too long.')        
        self.xfer = self.xfer + len(data)
        dibs_logger.Logger.PrintAndLog('SocketTransmit sending "' +
                                       data[0:200] +
                                       '"\n(only first 200 characters shown)',
                                       dibs_logger.LOG_DEBUG)
        self.conn.send(data)
        dibs_logger.Logger.PrintAndLog('SocketTransmit: finished send',
                                       dibs_logger.LOG_DEBUG)
        
    def SocketReceive(self,size,attempts=0):
        self.conn.setblocking(0)
        endTime = time.time() + dibs_options.daemonTimeout
        data = ''
        amountReceived = 0
        dibs_logger.Logger.PrintAndLog('SocketReceive: trying to receive',
                                       dibs_logger.LOG_DEBUG)
        while (time.time() < endTime and amountReceived < size):
            try:
                buf = self.conn.recv(size)
                data = data + buf
                amountReceived = amountReceived + len(buf)
            except socket.error, (num, type):
                if (socketErrsToIgnore.count(type)):
                    # not really an error, just no data
                    pass
                else:
                    raise DIBSUnexpectedSocketError, (
                        dibs_options.errorDir,dibs_options.dibsAdmin,num, type)
        if (amountReceived < size):
            if (amountReceived > 0):
                # We got a timeout after receiving only part of the data
                # that is bad so complain about it.
                raise DIBSRecvTimeout, (dibs_options.errorDir,
                                        dibs_options.dibsAdmin,
                                        size,amountReceived)
            elif (amountReceived == 0):
                # peer was busy so throw an exception and try again later
                self.status = 0 # prevents us from transmitting further
                raise PeerBusyException
        else:
            dibs_logger.Logger.PrintAndLog('SocketReceive: recieve successful',
                                           dibs_logger.LOG_DEBUG)
        self.conn.setblocking(1)
        return data

    def SaveToIncoming(self,data):
        fileName = (PathJoin(dibs_options.incomingQueueDir,
                                 `round(time.time()*1000)`) +
                    HashToFileName(data))
        dibs_logger.Logger.PrintAndLog('Saving incoming file to ' + fileName,
                                       dibs_logger.LOG_DEBUG)
        fd = open(fileName,'wb')
        fd.write(data.replace('\r',''))
        fd.close()

    def ExpectResponse(self,regexp):
        cmd = self.SocketReceive(dibs_constants.daemonCmdSize)
        dibs_logger.Logger.PrintAndLog('cmd is ' + `cmd`,
                                       dibs_logger.LOG_DEBUG)
        m = regexp[1].match(cmd)
        if (not m):
            raise DIBSUnexpectedResponse, (dibs_options.errorDir,
                                           dibs_options.dibsAdmin,
                                           cmd,regexp[0])
        return m

    def DeliverFile(self,file):
        fd = open(file,'rb')
        self.SocketTransmit('INCOMING_FILE ' + `os.path.getsize(file)`)
        self.SocketTransmit(fd.read(),pad=0)
        self.ExpectResponse(rOK)
        dibs_logger.Logger.PrintAndLog('got OK response in DeliverFile',
                                       dibs_logger.LOG_DEBUG)
        fd.close()
        os.remove(file)

class DIBSServer(DIBSCommunicator):

    def __init__(self,port):
        self.xfer = 0
        self.stopTime = None
        self.lastPoll = time.time()
        self.lastProbeTime = time.time()
        self.lastSendAttempt = time.time()
        self.cmdTable = { 'GIVE' : self.ProcessGive,
                          'GET' : self.ProcessGet,
                          'FINISHED' : self.ProcessFinished,
                          'HELLO' : self.ProcessHello,
                          'HELO' : self.ProcessHello
                          }
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.s.bind(('', port))
        self.s.listen(1)
        self.conn, self.connAddr = None, None
        while self.DaemonStayAlive():
            self.DoPeriodicChecks()
            r = select.select([self.s],[self.s],[self.s],
                              dibs_options.daemonTimeout)
            if (r[0] or r[1] or r[2]):
                self.xfer = 0
                statsDatabase = dibs_statistics.DIBSStatDatabase()
                self.conn, self.connAddr = self.s.accept()
                dibs_logger.Logger.PrintAndLog('Connected by ' +
                                               `self.connAddr`,
                                               dibs_logger.LOG_INFO)
                try:
                    while (self.ProcessCommand() != 0):
                        pass
                    statsDatabase.NoteConnectionFrom(self.connAddr[0],None,
                                                     self.xfer)
                except DIBSDaemonException, de:
                    de.Report()
                    statsDatabase.NoteConnectionFrom(self.connAddr[0],de,
                                                     self.xfer)

                statsDatabase.DumpToFile(PathJoin(
                    dibs_options.statsMsgDir,`time.time()`))
                dibs_logger.Logger.PrintAndLog('Connection from ' +
                                               `self.connAddr` + ' closed.',
                                               dibs_logger.LOG_INFO)
                self.conn.close()
                self.SpawnCommand('process_message')                

            self.DoPeriodicChecks()

        dibs_logger.Logger.PrintAndLog('Stopping daemon.\n',
                                       dibs_logger.LOG_INFO)
                
    def __del__(self):
        self.s.close()

    def DoPeriodicChecks(self):
        if (time.time() - self.lastPoll > dibs_options.pollInterval):
            dibs_logger.Logger.PrintAndLog('Doing periodic checks...',
                                           dibs_logger.LOG_INFO)
            self.lastPoll = time.time()
            self.SpawnCommand('auto_check')
            self.SpawnCommand('send_message')
            self.SpawnCommand('poll_passives')
            self.SpawnCommand('process_message')
            self.SpawnCommand('merge_stats')
            self.MaybeDoRandomProbe()

    def SpawnCommand(self,cmd):

        # Use P_WAIT because process_message will require database
        # locks so there is no sense in parallizing it.
        
        if (not os.path.exists(dibs_options.lockfile)):
            dibs_logger.Logger.PrintAndLog('Spawning ' + `cmd` + '.\n',
                                           dibs_logger.LOG_INFO)
            os.spawnl(os.P_WAIT,dibs_options.pythonExe,dibs_options.pythonExe,
                      dibs_options.dibsExe,cmd)
            return 1
        else:
            print ('[' + `time.asctime(time.localtime(time.time()))`
                   + ']: Not spawning ' + `cmd` +
                ' since database locked, try again later.\n')
            MailUserIfLockfileTooOld(dibs_options.lockfile,
                                     dibs_options.dibsAdmin,
                                     dibs_options.smtpServer)
            return 0

    def MaybeDoRandomProbe(self):
        if (time.time() - self.lastProbeTime >= dibs_options.probePeriod):
            if (self.SpawnCommand('probe')):
                self.lastProbeTime = time.time()

    def DaemonStayAlive(self):
        """
        Returns true if the Daemon should stay alive and wait for
        connections and false if the Daemon should exit.  To stop
        the Daemon just create the file dibs_options.daemonStopFile.
        To stop after a delay of x seconds put x in the file
        dibs_options.daemonStopFile.
        """

        if (self.stopTime):
            if (time.time() <= self.stopTime):
                dibs_logger.Logger.PrintAndLog('Executing delayed stop.\n',
                                               dibs_logger.LOG_INFO)
                return 0
            else:
                return 1
        if (os.path.exists(dibs_options.daemonStopFile)):
            fd = open(dibs_options.daemonStopFile,'rb')
            delay = string.strip(fd.read())
            fd.close()
            os.remove(dibs_options.daemonStopFile)
            if (delay):
                delay = float(delay)
                self.stopTime = time.time() + delay
                dibs_logger.Logger.PrintAndLog('Will stop in ' + `delay` +
                                               ' seconds.\n',
                                               dibs_logger.LOG_INFO)
                return 1
            else:
                dibs_logger.Logger.PrintAndLog('Executing immediate stop.\n',
                                               dibs_logger.LOG_INFO)
                return 0
        else:
            return 1

    def ProcessCommand(self):
        match = self.ExpectResponse(rCmd)
        return self.cmdTable[match.group('cmd')](match)

    def ProcessFinished(self,match):
        return 0

    def ProcessHello(self,match):
        self.SocketTransmit('DIBS VERSION = ' + dibs_constants.version_string +
                            '\nsee http://dibs.sourceforge.net for more info.')
        return 1
    
    def ProcessGet(self,match):
        assert match.group('arg1'), 'Need email address arg for GET command.'

        dir = match.group('arg1')
        path = PathJoin(dibs_options.outgoingQueueDir,dir)
        if (os.path.exists(path)):
            for file in os.listdir(path):
                self.DeliverFile(PathJoin(path,file))
        self.SocketTransmit(sOK)
        return 1

    def ProcessGive(self,match):
        filesReceived = 0
        while 1:
            match = self.ExpectResponse(rOKorI)
            if (match.group('ok')):
                dibs_logger.Logger.PrintAndLog('GET finished after receiving '
                                               + `filesReceived` + ' files.',
                                               dibs_logger.LOG_INFO)
                break
            else:
                filesReceived = filesReceived + 1
                self.SaveToIncoming(self.SocketReceive(
                    long(match.group('arg1'))))
                self.SocketTransmit(sOK)
                dibs_logger.Logger.PrintAndLog('Sent OK after receiving file',
                                               dibs_logger.LOG_DEBUG)


class DIBSClient(DIBSCommunicator):        
    def __init__(self,peer,host,port):
        # Convert port to an integer.  This is a HACK.  We should really
        # make sure that we store the port as an integer when the 
        # add_peer command is issued, but making that change would
        # break compatiability so wait until next major release for that.
        port = int(port)
        self.xfer = 0
        self.peer = peer
        try:
            dibs_logger.Logger.PrintAndLog('Connecting to ' +
                                           host + ':' + `port`,
                                           dibs_logger.LOG_INFO)
            self.statsDatabase = dibs_statistics.DIBSStatDatabase()
            self.host = host
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect((host,port))
            self.status = 1
        except socket.error, (errno,msg):
            self.status = 0
            self.statsDatabase.NoteConnectionTo(self.peer,(errno,msg),0)
            self.statsDatabase.DumpToFile(PathJoin(dibs_options.statsMsgDir,
                                                   `time.time()`))
            
            if (socketErrsToIgnore.count(string.strip(msg))):
                dibs_logger.Logger.PrintAndLog('Connection failed due to ' +
                                        'socket error: (' +
                                        `errno` + ', ' + msg + ')',
                                               dibs_logger.LOG_ERROR)
            else:
                raise DIBSException, ('Unexpected socket error: (' +
                                      `errno` + ', ' + msg + ')')
                
    def Ok(self):
        return self.status

    def __del__(self):
        if (self.Ok()): # Only send finished message if socket still ok
            self.TransmitFinished()
        self.conn.close()
        if (self.Ok()): # if not OK, statsDatabase already dumped
            self.statsDatabase.NoteConnectionTo(self.peer,None,self.xfer)
            self.statsDatabase.DumpToFile(PathJoin(dibs_options.statsMsgDir,
                                                   `time.time()`))


    def TransmitHello(self):
        self.SocketTransmit('HELLO')
        return self.SocketReceive(dibs_constants.daemonCmdSize)

    def TransmitFinished(self):
        dibs_logger.Logger.PrintAndLog('Doing TransmitFinished',
                                       dibs_logger.LOG_DEBUG)
        self.SocketTransmit('FINISHED')

    def TransmitGive(self,files):
        cmd = 'GIVE '
        dibs_logger.Logger.PrintAndLog('Doing TransmitGive:' + cmd,
                                       dibs_logger.LOG_DEBUG)
        self.SocketTransmit(cmd)
        for file in files:
            try:
                self.DeliverFile(file)
            except PeerBusyException, e:
                dibs_logger.Logger.PrintAndLog('Could not send file ' + `file`
                                               + ' due to PeerBusyException: '
                                               + `e` + '.\n',
                                               dibs_logger.LOG_WARNING)
                return
            except Exception, e:
                tempName = tempfile.mktemp()
                dibs_logger.Logger.PrintAndLog('Could not send file ' + `file`
                                               + ' due to exception: ' + `e`
                                               + '\nMoving it to ' + tempName,
                                               dibs_logger.LOG_CRITICAL)
                dibs_utils.MoveFile(file,tempName)
                raise e

        self.SocketTransmit(sOK)

    def TransmitGet(self):
        cmd = 'GET ' + dibs_options.dibsPublicKey
        dibs_logger.Logger.PrintAndLog('Doing TransmitGet:' + cmd,
                                       dibs_logger.LOG_INFO)
        self.SocketTransmit(cmd)
        filesReceived = 0
        while 1:
            match = self.ExpectResponse(rOKorI)
            if (match.group('ok')):
                dibs_logger.Logger.PrintAndLog('GET finished after receiving '
                                               + `filesReceived` + ' files.',
                                               dibs_logger.LOG_INFO)
                break
            else:
                filesReceived = filesReceived + 1
                self.SaveToIncoming(self.SocketReceive(
                    long(match.group('arg1'))))
                self.SocketTransmit(sOK)

