
import os
import dibs_options
from templates import *
from dibs_utils import *

class PollPassivesCmd(DIBSCommand):
    """
    Contact all peers who are passive and get any messages they
    have for us.
    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

    def run(self,argv=None,parentWindow=None):
        
        self.PrepareForDIBSCommand()
        
        if (None != argv):
            self.ParseRequiredArgs(argv)
        
        import dibs_daemon

        for peer in self.database.GetPassivePeers():
            c = dibs_daemon.DIBSClient(peer[0],peer[1].host,peer[1].port)
            if (c.Ok()):
                c.TransmitGet()

        self.FinishDIBSCommand()

class StartDaemonCmd(DIBSCommand):

    """
    This command starts the DIBS daemon.

    The daemon must be running for DIBS to automatically send and
    respond to messages from peers and to automatically backup the
    data you place in the directory named by the autoBackupDir option
    (default is .dibs/autoBackup).  For more information about the
    DIBS daemon, see the DIBS manual.
    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

    def run(self,argv=None,parentWindow=None):
        if (None != argv):
            self.ParseRequiredArgs()

        print 'Spawning Daemon.'
        os.spawnl(os.P_NOWAIT,dibs_options.pythonExe,dibs_options.pythonExe,
                  dibs_options.dibsExe,'start_daemon')
        print 'Daemon is alive.'


class StopDaemonCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        import dibs_daemon

        fd = open(os.path.join(dibs_options.DIBS_DIR,'stop_daemon'),'w')
        fd.close()

        host = '127.0.0.1'
        port = `dibs_options.daemonPort`
        c = dibs_daemon.DIBSClient(None,host,port)        
        location =  host + ':' + `port`
        if (c.Ok()):
            print 'Asking daemon at ' + location + ' to stop.\n'
            c.TransmitHello()
        else:
            print 'Failed to reach daemon at ' + location + '.\n'

class SendHelloCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.RequiredArg('host=',StringValidator(),"""
        Specifies the host to contact. 
        """)
        self.RequiredArg('port=',IntegerValidator(),"""
        Specifies the port to use. 
        """)

    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        import dibs_daemon

        c = dibs_daemon.DIBSClient(None,self['host'],self['port'])
        if (c.Ok()):
            print 'Sending HELLO to ' + self['host'] + ':' + `self['port']`
            result = c.TransmitHello()
            print 'Response to HELLO:\n' + result + '\n'
        else:
            print 'Failed to connect to ' + self['host'] + ':' + self['port']



class ProcessMessageCmd(DIBSCommand):
    """
    Process an incoming message named by file, or if no file argument
    is given try to process all messages in the incoming directory.

    We assign the global variable gFileToMoveOnError to be the file to
    process.  If an exception is raised, the calling code will move
    the file named by this global variable to a temporary location.
    This is so that we don't keep trying to process a message which
    is causing an error and end up mail-bombing the user with error
    messages.
    """
    
    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.OptionalArg('file=',ExistingFileNameValidator(
            initialDir=dibs_options.incomingQueueDir),"""
        Name of message file to process.
        """)


    def run(self,argv=None,parentWindow=None):

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        
        if (None != argv):
            self.ParseRequiredArgs(argv)
        
        if (None != self['file'] and '' != self['file'].strip()):
            files = [self['file']]
        else:
            dir = dibs_options.incomingQueueDir
            files = map(lambda x: PathJoin(dir,x),os.listdir(dir))

        if (len(files) <= 0):
            d.PrintAndLog('No messages to process.')
        else:
            for file in files:
                global gFileToMoveOnError
                gFileToMoveOnError = file
                d.ProcessMessage(file)
                d.PrintAndLog('Processed msg in file ' + `file` + '.')
                d.database.SaveToFile(dibs_options.databaseFilePrefix)
                os.remove(file)

        self.FinishDIBSCommand()

class SendMessageCmd(DIBSCommand):
    """
    If both file and peer are absent, then try to send all outgoing
    messages.
    
    Otherwise send an outgoing message named by file to the peer named by peer.
    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.OptionalArg('file=',ExistingFileNameValidator(
            initialDir=dibs_options.outgoingQueueDir),"""
        Name of file to send.
        """)

        self.OptionalArg('peer=',StringValidator(),"""
        Name of peer to send file to.
        """)

    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        if ( (not self['file']) and (not self['peer']) ):
            d.SendOutgoingMessages()
        elif ( self['file'] and self['peer'] ):
            d.SendMessage(self['file'],self['peer'])
        else:
            raise Exception, ('Either both or neither file and peer ' +
                              'should be specified.')

        self.FinishDIBSCommand()

