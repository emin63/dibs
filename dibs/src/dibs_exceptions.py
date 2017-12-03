
import dibs_options
import dibs_logger
import dibs_utils
import string, sys

class DIBSException(Exception):
    def __init__(self,msg):
        self.msg = msg
        self.exc_info = sys.exc_info()
        self.Report()

    def __str__(self):
        return 'DIBSException: ' + self.msg + \
               dibs_utils.GetTracebackString(self.exc_info)

    def Report(self):
        dibs_logger.Logger.LogError(self.__str__())

class DIBSUnhandledException(DIBSException):
    """
    This exception represents internal errors (e.g., divide by 0) or
    other errors which dibs does not know about.
    """

    def __init__(self,e):
        self.exc_info = sys.exc_info()
        self.msg = 'Internal error:\n' + e.__str__() + '\n occurred.\n'
        self.Report()

class BadSignature(DIBSException):
    def __init__(self,status,output):
        self.exc_info = sys.exc_info()
        self.msg = string.join(['Unable to verify digital signature.  ',
                                'Received status ',`status`,' and output:\n',
                                output,'.'],'')
        self.Report()
        

class DuplicateStorageRequestFromPeer(DIBSException):
    def __init__(self,dibsMsg):
        """
        This exception is raised when a peer tries to store a piece
        on our machine that we already have.
        """

        self.exc_info = sys.exc_info()
        self.msg = 'Request to store piece ' + dibsMsg.pieceName
        self.msg = 'failed because it is already stored.\n'
        self.Report()

class MessageExceedsQuota(DIBSException):
    def __init__(self,dibsMsg,quotaInfo):
        """
        This exception is raised when a peer tries to store a piece
        on our machine that goes above its storage quota.
        """
        self.exc_info = sys.exc_info()
        self.msg = 'Request to store piece ' + dibsMsg.pieceName
        self.msg = self.msg + 'denied due to quota limit.\n'
        self.msg = self.msg + 'Quota = ' + `quotaInfo[0]`
        self.msg = self.msg + ', Usage = ' + `quotaInfo[1]` + '\n'
        self.Report()

class NoPeersToTradeWith(DIBSException):
    def __init__(self):
        self.exc_info = sys.exc_info()
        self.msg = 'No peers exist in database with sufficient trading room.'
        self.Report()

class LocalFileNonExistent(DIBSException):
    """
    This exception is raised when we are trying to unstore a file which
    we gave to other people to store for us.  The exception means that
    we have no record of storing the specified file.

    By contrast, the RemoteFileNonExistent exception is raised when we
    are trying to unstore a file we are supposedly storing for somebody
    else.
    """

    def __init__(self,file):
        self.exc_info = sys.exc_info()
        self.msg = 'No record of storing file \'' + file + '\'.\n'
        self.Report()

class RemoteFileNonExistent(DIBSException):
    """
    This exception is raised when we are trying to unstore a piece which
    someone else thinks we are storing, but we can't find the specified
    piece on our system.
    
    """

    def __init__(self,pieceName):
        self.exc_info = sys.exc_info()
        self.msg = 'No record of storing piece \'' + pieceName + '\'.\n'
        self.Report()

class DuplicateStoreFileRequest(DIBSException):
    """
    This exception is raised when DIBS is asked to store a file which
    it has already distributed to other peers for storage.
    """

    def __init__(self,file):
        self.exc_info = sys.exc_info()
        self.msg = string.join(['Duplicate store request for file ',file,'.'],
                               '')
        self.Report()

class CouldNotParseDIBSMsg(DIBSException):

    def __init__(self,e,data):
        self.exc_info = sys.exc_info()
        self.msg = string.join(
            ['Unable to parse piece DIBS msg due to exception: ' + e.__str__(),
             '\nmessage was:\n' + data])
        self.Report()


class UnstoreIgnoredBecauseStaleTime(DIBSException):

    def __init__(self,unstoreCmdTime,storeCmdTime):
        self.exc_info = sys.exc_info()
        self.msg = string.join(['Unstore request ignored due to stale',
                                'command time.\n','Store cmd time =',
                                storeCmdTime,', unstore cmd time =',
                                unstoreCmdTime,'.\n',
                                'Please check you machine or email system',
                                'for clock skew or latency.'])
        self.Report()


class DIBSDaemonException(DIBSException):
    def Report(self):
        msg = dibs_utils.MailErrorMsgToUser(
            'DIBS DAEMON ERROR:\n\n' + self.msg,
            self.email,self.email,
            dibs_options.errWarnCount,dibs_options.errMaxCount,
            dibs_options.errorDir,dibs_options.smtpServer)
        if (msg):
            self.msg = self.msg + 'Error mailing user:\n' + msg
        DIBSException.Report(self)

class DIBSRecvTimeout(DIBSDaemonException):

    def __init__(self,logDir,email,size,amountReceived):
        self.logDir = logDir
        self.email = email
        self.exc_info = sys.exc_info()
        self.msg = string.join(['Timeout while trying to receive data.\n',
                                'Wanted',`size`,'bytes, but only got',
                                `amountReceived`,'bytes.\n'])
        self.Report()

class DIBSUnexpectedSocketError(DIBSDaemonException):

    def __init__(self,logDir,email,num,type):
        self.logDir = logDir
        self.email = email
        self.exc_info = sys.exc_info()
        self.msg = 'Unexpected socket error: ' + `num` + ' ' + `type` + '.\n'
        self.Report()


class DIBSUnexpectedResponse(DIBSDaemonException):

    def __init__(self,logDir,email,cmd,expected):
        self.logDir = logDir
        self.email = email
        self.exc_info = sys.exc_info()
        self.msg = string.join(['Unexpected protocol response "',
                                cmd,'".\n',
                                'Expected response form was "',
                                expected,'".\n'])
        self.Report()


class UnknownPeerException(DIBSException):

    def __init__(self,peer):
        self.exc_info = sys.exc_info()
        self.msg = 'No record of peer "' + peer + '" in database.\n'
        self.Report()

class NonZeroStoragePreventsDelete(DIBSException):

    def __init__(self,peer,remoteStorage,localStorage):
        self.exc_info = sys.exc_info()
        self.msg = ('Entry for peer ' + peer + ' has non-zero storage.\n' +
                    'local storage = ' + `localStorage`
                    + ', remote storage = ' + `remoteStorage` + '.\n'
                    'Use the "clear" or "forget" command to zero storage.\n')
        self.Report()

class NoBigDealException(DIBSDaemonException):
    def __init__(self):
        self.exc_info = sys.exc_info()
        self.msg = 'No big deal exception.'

    def __str__(self):
        # All NoBigDealException objects must have their __str__ method
        # start with the string 'NoBigDealException' so that we can
        # detect this in other parts of the code.
        return 'NoBigDealException'

class PeerBusyException(NoBigDealException):
    def __init__(self):
        self.msg = 'Peer busy, wait until later.'
    
    def Report(self):
        dibs_logger.Logger.PrintAndLog(self.msg,dibs_logger.LOG_WARNING)

class PostContractFailed(DIBSException):
    def __init__(self,contract,url,response):
        self.exc_info = sys.exc_info()        
        self.msg = ('Failed to post contract\n' + contract.__str__() + 
                    '\nresponse from contract server at ' + url +
                    '\nis\n' + response)
        self.Report()

class UnpostContractFailed(DIBSException):
    def __init__(self,contract,url,response):
        self.exc_info = sys.exc_info()        
        self.msg = ('Failed to post contract\n' + contract + 
                    '\nresponse from contract server at ' + url +
                    '\nis\n' + response)
        self.Report()

class PeerDirExistsException(DIBSException):
    def __init__(self,peerDirName,peer):
        self.exc_info = sys.exc_info()        
        self.msg = ('Could add peer ' + `peer` + ' because the directory\n' +
                    `peerDirName` + ' already exists for that peer.\n' +
                    'Probably this directory was created by an earlier failed\n'
                    + 'attempt to add this peer. Please delete this directory\n'
                    + 'and try your command again.\n')
        self.Report()
