import re, string, time, xml, xml.parsers, xml.parsers.expat


import dibs_constants
import dibs_crypto
import dibs_options

from dibs_exceptions import *

def GetArg(str,argName):
    m = re.search('{ *.*' + argName + ' +"([^}"]+)".*}',str,re.DOTALL)
    if (not m):
        return ''
    else:
        return m.group(1)

def GetDIBSAdmin(header):
    m = re.search('(?m)^' + dibs_constants.adminField + ' *(.+)$',header)
    if (not m):
        return ''
    else:
        return m.group(1)

def GetSender(header):
    m = re.search('(?m)^From: *.*<([^>]+)>.*$',header)
    if (not m):
        return 'UNKNOWN'
    else:
        return m.group(1)

def GetDIBSField(header,field):
    m = re.search('(?m)^' + field +' *(.+)$',header)
    if (not m):
        return None
    else:
        return m.group(1)    

def GetHeaderAndMsgFromFile(fileName):
    "Take a file representing an email and extract the header and msg."

    fd = open(fileName,'rU')
    data = fd.read()
    fd.close()
    i = string.find(data,'\n\n')
    return (data[0:i],data[(i+1):])

def MakeStartTag(tagName,attrs={}):
    result = '<' + tagName
    for key in attrs.keys():
        result += ' ' + key + '="' + attrs[key] + '"'
    result += '>'
    return result

def MakeEndTag(tagName):
    return '</' + tagName + '>'

def MakeEndCmdTag():
    return MakeEndTag(dibs_constants.cmdTagName)

class DIBSMsg:

    def __init__(self,msgFile):
        """
        This class represents the pieces of an email parsed into
        fields relevant to DIBS.

        REQUIRE PROPERTIES: cmdTime
        -----------------------------------------------------------
        The object will always provide the property self.cmdTime to
        represent the time the message was created as returned by
        time.time()
        -----------------------------------------------------------
        
        OPTIONAL PROPERTIES: pieceName, payload
        -----------------------------------------------------------
        If a piece name is present it is provided under self.pieceName.
        If a payload is present (e.g., the piece named by pieceName),
        then it is provided as self.payload.
        -----------------------------------------------------------

        If an error occurs in parsing, (e.g., a bad digital signature
        or a mangled dibs command, then the appropriate exception
        is thrown and an email is sent to the sender.
        """

        (self.header, self.msg) = GetHeaderAndMsgFromFile(msgFile)
        self.trueSender = GetSender(self.header)
        self.dibsAdmin = GetDIBSAdmin(self.header)
        self.ParseCommandAndArgs(self.msg)

    def ParseCommandAndArgs(self,data):
        self.args = {}
        self.currentTagID = ''
        self.currentTagData = ''
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.StartElement
        self.parser.EndElementHandler = self.EndElement
        self.parser.CharacterDataHandler = self.ParseCharacterData
        self.tagParsers = {dibs_constants.cmdTagName : self.ParseCommand,
                           dibs_constants.argTagName : self.ParseArg}
        try:
            startPoint = data.index('<' + dibs_constants.cmdTagName)
            endPoint = (len(MakeEndCmdTag()) + data.index(MakeEndCmdTag()))
            self.parser.Parse(data[startPoint:endPoint])
        except Exception, e:
            raise CouldNotParseDIBSMsg, (e,data)

        ### Map required arguments from message to properties of object
        self.cmdTime = self.args[dibs_constants.cmdTimeArgName]

        ### Map existing optional args from message to properties of object
        if (self.args.has_key(dibs_constants.pieceDataArgName)):
            self.payload = dibs_utils.AddPGPHeaders(self.args[
                dibs_constants.pieceDataArgName])
        if (self.args.has_key(dibs_constants.pieceNameArgName)):
            self.pieceName = self.args[dibs_constants.pieceNameArgName]
        

    def StartElement(self,name, attrs):
        if (self.tagParsers.has_key(name)):
            return self.tagParsers[name](attrs)
        else:
            raise 'unknown tag ' + `name` + ' seen'

    def ParseCommand(self,attrs):
        if (len(attrs) > 1 or not attrs.has_key('id')):
            raise (dibs_constants.cmdTagName + ' tag has wrong many attributes: ' + `attrs`)
        else:
            self.cmd = attrs['id']
        
    def ParseArg(self,attrs):
        if (len(attrs) > 1 or not attrs.has_key('id')):
            raise (dibs_constants.argTagName +
                   ' tag has wrong many attributes: ' + `attrs`)
        else:
            self.currentTagID = attrs['id']
            self.currentTagData = ''

    def ParseCharacterData(self,data):
        self.currentTagData += data
        
    def EndElement(self,name):
        if (dibs_constants.argTagName == name):
            self.args[self.currentTagID] = self.currentTagData
            self.currentTagID = ''
            self.currentTagData = ''


    def __str__(self):

        msg = 'TRUE SENDER = ' + self.trueSender + '\n'
        msg = msg + 'COMMAND = ' + self.cmd + '\n'
        return msg
        
##############################################################
#
# Functions below are for creating various messages which the
# receiver's dibs program will process
#

def MakeMsgHeader(peer,subject):
    """
    Take a peer name and a subject and return a header for
    the corresponding dibs message.
    """

    return (dibs_constants.adminField + ' ' + dibs_options.dibsAdmin +
            '\n' + dibs_constants.dibsToField + ' ' + peer + '\n' +
            'Subject: <DIBS> ' + subject + '\n\n')

    
def MakeMsgCmd(cmdName,argList):
    """
    Take a command name and an argList of tuples consisting of
    pairs of the form (argName, argValue), and return a string
    representing the corresponding dibs command.
    """

    body = MakeStartTag(dibs_constants.cmdTagName,{'id':cmdName}) + '\n'
    for argPair in argList:
        body += (MakeStartTag(dibs_constants.argTagName,{'id':argPair[0]})
                 + argPair[1] + MakeEndTag(dibs_constants.argTagName) + '\n')
    body += (MakeStartTag(dibs_constants.argTagName,
                          {'id':dibs_constants.cmdTimeArgName})
             + `time.time()` + MakeEndTag(dibs_constants.argTagName) + '\n' +
             MakeEndCmdTag())

    return body

def CreateProbeResponseHeaderAndBody(pieceName,peer,data):

    hdr = MakeMsgHeader(peer,'DIBS PROBE RESPONSE')
    
    body = MakeMsgCmd(dibs_constants.probeResponseCmdName,
                      ((dibs_constants.pieceNameArgName, pieceName),
                       (dibs_constants.pieceDataArgName,
                        dibs_utils.RemovePGPHeaders(data))))

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)

def CreateProbeRequestHeaderAndBody(pieceName,peer):

    hdr = MakeMsgHeader(peer,'DIBS PROBE REQUEST')

    body = MakeMsgCmd(dibs_constants.probeCmdName,
                      ((dibs_constants.pieceNameArgName, pieceName),))

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)


def CreateRecoverResponseHeaderAndBody(pieceName,peer,data):

    hdr = MakeMsgHeader(peer,'DIBS RECOVER RESPONSE')
    
    body = MakeMsgCmd(dibs_constants.recoverResponseCmdName,
                      ((dibs_constants.pieceNameArgName, pieceName),
                       (dibs_constants.pieceDataArgName,
                        dibs_utils.RemovePGPHeaders(data))))

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)

def CreateRecoverRequestHeaderAndBody(pieceName,peer):

    hdr = MakeMsgHeader(peer,'DIBS RECOVER REQUEST')

    body = MakeMsgCmd(dibs_constants.recoverCmdName,
                      ((dibs_constants.pieceNameArgName, pieceName),))

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)

def CreateRecoverAllRequestHdrAndBdy(peer):

    hdr = MakeMsgHeader(peer,'DIBS RECOVER ALL REQUEST')

    body = MakeMsgCmd(dibs_constants.recoverAllCmdName,[])

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)

def CreateRecoverAllFinishedHdrAndBdy(peer):

    hdr = MakeMsgHeader(peer,'DIBS FINISHED RECOVER ALL REQUEST')

    body = MakeMsgCmd(dibs_constants.doneRecoverAllCmdName,[])

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)


def CreateUnstoreHeaderAndBody(pieceName,peer):

    hdr = MakeMsgHeader(peer,'DIBS UNSTORE REQUEST')
    
    body = MakeMsgCmd(dibs_constants.unstoreCmdName,
                      ((dibs_constants.pieceNameArgName, pieceName),))

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)

def CreateClearDBHeaderAndBody(peer):

    hdr = MakeMsgHeader(peer,'DIBS CLEAR REQUEST')
    
    body = MakeMsgCmd(dibs_constants.clearCmdName, ())

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)

def CreateForgetYouMsg(peer):
    hdr = MakeMsgHeader(peer,'DIBS FORGET YOU')
    body = MakeMsgCmd(dibs_constants.forgetYouCmdName, ())

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)

def CreateStoreHeaderAndBody(peer,data,pieceName):
    """
    Prepare an email to peer requesting storage of 
    encryptedFile under the name pieceName.

    Returns header and body of email.
    """

    hdr = MakeMsgHeader(peer,'DIBS STORE REQUEST')

    body = MakeMsgCmd(dibs_constants.storeCmdName,
                      ((dibs_constants.pieceNameArgName, pieceName),
                       (dibs_constants.pieceDataArgName,
                        dibs_utils.RemovePGPHeaders(data))))

    body = dibs_crypto.SignPiece(body,peer)

    return (hdr,body)



def CreatePeerProposalHeaderAndBody(peer,contractName,talkType,listenType,
                                    proposedRemoteQuota,
                                    proposedLocalQuota,
                                    hostName):
    """
    The CreatePeerProposalHeaderAndBody function creates a message
    to propose a contract to the peer.  All the inputs to this function
    are from the point of view of the peer we are proposing to.  For
    example, the talkType is what the peer would use as the argument
    to --talk and the proposedRemoteQuota is what the peer would use
    as the argument to --remote_quota in the add_peer function.

    """
    hdr = MakeMsgHeader(peer,'DIBS CONTRACT PROPOSAL')

    pubKey = dibs_utils.RemovePGPHeaders(
        dibs_crypto.GetPubKey(),dibs_constants.pgpKeyStart,
        dibs_constants.pgpKeyEnd)
    

    body = MakeMsgCmd(dibs_constants.proposalCmdName,(
        (dibs_constants.contractNameArgName, contractName),
        (dibs_constants.adminArgName, dibs_options.dibsAdmin),
        (dibs_constants.talkTypeArgName, talkType),
        (dibs_constants.listenTypeArgName, listenType),
        (dibs_constants.remoteQuotaArgName, `proposedRemoteQuota`),
        (dibs_constants.localQuotaArgName, `proposedLocalQuota`),        
        (dibs_constants.hostArgName, hostName),
        (dibs_constants.portArgName, `dibs_options.daemonPort`),
        (dibs_constants.publicKeyNameArgName, dibs_options.dibsPublicKey),
        (dibs_constants.publicKeyArgName, pubKey)
        ))

    body = dibs_crypto.SignPiece(body,peer)
                      
    return (hdr,body)

def CreateProposalResponseHeaderAndBody(peer,contractName,acceptedP,comment):
    hdr = MakeMsgHeader(peer,'DIBS PROPOSAL RESPONSE')

    assert acceptedP == 'YES' or acceptedP == 'NO'

    body = MakeMsgCmd(dibs_constants.proposalResponseCmdName,(
        (dibs_constants.contractNameArgName, contractName),
        (dibs_constants.proposalDecisionArgName, acceptedP),
        (dibs_constants.proposalCommentArgName, comment)))

    body = dibs_crypto.SignPiece(body,peer)
                      
    return (hdr,body)
