
import math
import string
import tempfile
import sys
import re
import os, os.path
import time
import smtplib
from dibs_mod_commands import getstatusoutput

import dibs_constants
import dibs_options 
import dibs_database
import dibs_logger
import dibs_daemon
import dibs_crypto
import dibs_msg
import dibs_link
import dibs_contract

from ffield import file_ecc

from dibs_utils import *
from dibs_exceptions import *


class DIBS:
    "The main class which handles all dibs operations."

    # The StoreFileForPeer, ProbeFileForPeer, and other methods
    # in in CmdHandler must come before the definition of the
    # __init__ method so that these names are defined when
    # we define the CmdHandler dictionary.
            
    def StoreFileForPeer(self,dibsM,peer):
        if (len(dibsM.payload) > \
            self.database.RemainingQuotaForPeerOnOurMachine(peer)):
            raise MessageExceedsQuota, (dibsM,\
                                        self.database.QuotaForPeer(peer))
        else:
            self.database.RememberStoringPieceForPeerOnOurMachine(dibsM,peer)
            fileName = self.database.GetNameForPeerFile(dibsM.pieceName,peer)
            WriteToFile(dibsM.payload,fileName)


    def ClearDBForPeer(self,dibsM,peer):
        self.database.ForgetPeersPieces(peer)
            
    def UpdatePeerForgettingUs(self,dibsM,peer):
        """
        A peer just told us he forgot our data.
        """

        filesAffected = self.database.PeerForgotUs(peer)
        if (filesAffected):
            MailDataToUser('Peer ' + peer + ' forgot our files.\n' +
                           'The following files were affected and should'
                           + ' probably be recovered or unstored:\n'
                           + `filesAffected`,
                           dibs_options.dibsAdmin,dibs_options.dibsAdmin,
                           dibs_options.smtpServer)

    def UnstoreFileForPeer(self,dMsg,peer):
        """
        Remove the piece indicated in the dMsg for peer.
        """

        pieceName = dMsg.pieceName
        fileName = self.database.GetNameForPeerFile(dMsg.pieceName,peer)
        dibs_logger.Logger.PrintAndLog('Trying to unstore piece ' + pieceName +
                                       ' requires unstoring file ' +
                                       fileName + '.\n',
                                       dibs_logger.LOG_DEBUG)
        if (not os.path.exists(fileName)):
            raise RemoteFileNonExistent, pieceName
        pieceSize = os.path.getsize(fileName)

        # exception will be raised here if the cmdTime for the unstore is
        # before the time for the store.
        self.database.UnstorePieceForPeerOnOurMachine(
            peer,pieceName,pieceSize,dMsg.cmdTime)

        dibs_logger.Logger.PrintAndLog('going to remove ' +
                                       fileName + '.\n',dibs_logger.LOG_DEBUG)
        os.remove(fileName)

    def RecoverAllForPeer(self,dMsg,peer):
        dibs_logger.Logger.PrintAndLog('Starting to send back all data to ' +
                                       'peer '+`peer`+' for recover all.',
                                       dibs_logger.LOG_INFO)
        for pieceName in self.database.GetPiecesForPeer(peer):
            fileName = self.database.GetNameForPeerFile(pieceName,peer)
            fd = open(fileName,'rU')
            (hdr,body) = dibs_msg.CreateRecoverResponseHeaderAndBody(
                pieceName,peer,fd.read())
            fd.close()
            self.SendDataToPeer(hdr + body,peer)
        dibs_logger.Logger.PrintAndLog('Finished sending back all data to ' +
                                       'peer '+`peer`+' for recover all.',
                                       dibs_logger.LOG_INFO)
        (hdr,body) = dibs_msg.CreateRecoverAllFinishedHdrAndBdy(peer)
        self.SendDataToPeer(hdr + body,peer)        


    def RecoverFileForPeer(self,dMsg,peer):
        """
        Send piece indicated in the dMsg back to peer.
        """

        pieceName = dMsg.pieceName
        fileName = self.database.GetNameForPeerFile(dMsg.pieceName,peer)
        dibs_logger.Logger.PrintAndLog('Sending piece ' + pieceName +
                                       ' stored in file ' +
                                       fileName + ' back to peer.\n',
                                       dibs_logger.LOG_DEBUG)

        fd = open(fileName,'rU')
        (hdr,body) = dibs_msg.CreateRecoverResponseHeaderAndBody(
            pieceName,peer,fd.read())
        fd.close()

        self.SendDataToPeer(hdr + body,peer)

    def HandleRecoverResponseFromPeer(self,dMsg,peer):
        pieceName = dMsg.pieceName
        (file,pieceNum,dir,name)=self.GetRecoveryNamesAndNumbers(pieceName)
        if (not os.path.exists(dir)):
            os.makedirs(dir)
        if (self.database.StillNeedToRecover(file)):
            dirPlusName = PathJoin(dir,name)
            tempName = dirPlusName + '.tmp'
            dibs_logger.Logger.PrintAndLog('Storing piece ' + pieceName +
                                           ' in file ' + dirPlusName + 
                                           ' for recovery.\n',
                                           dibs_logger.LOG_DEBUG)
            fd = open(tempName,'wU')
            fd.write(dMsg.payload)
            fd.close()
            dibs_crypto.DecryptFileToFile(tempName,dirPlusName)
            os.remove(tempName)
            done = self.database.RememberPieceOfFileRecovered(file,pieceNum,
                                                              dirPlusName)
            if (done):
                self.FinishRecoveryByCombiningPieces(file)
        else:
            dibs_logger.Logger.PrintAndLog('Ignoring piece ' + pieceName +
                                           ' of file ' + file
                                           + ' because recovery complete.',
                                           dibs_logger.LOG_DEBUG)


    def HandleRecoverAllResponseFromPeer(self,dMsg,peer):
        pieceName = dMsg.pieceName
        (file,pieceNum,dir,name)=self.GetRecoveryNamesAndNumbers(pieceName)
        if (self.database.StillNeedToRecover(file)):
            dirPlusName = PathJoin(dir,name)
            tempName = dirPlusName + '.tmp'
            dibs_logger.Logger.PrintAndLog('Storing piece ' + pieceName +
                                           ' in file ' + dirPlusName + 
                                           ' for recovery.\n',
                                           dibs_logger.LOG_DEBUG)
            fd = open(tempName,'wU')
            fd.write(dMsg.payload)
            fd.close()
            dibs_crypto.DecryptFileToFile(tempName,dirPlusName)
            os.remove(tempName)
            done = self.database.RememberPieceOfFileRecovered(file,pieceNum)
            if (done):
                self.FinishRecoveryByCombiningPieces(file)
        else:
            dibs_logger.Logger.PrintAndLog('Ignoring piece ' + pieceName +
                                           ' of file ' + file
                                           + ' because recovery complete.',
                                           dibs_logger.LOG_DEBUG)

    def HandleRecoverAllFinishedFromPeer(self,dMsg,peer):
        self.database.PeerDoneRespondingToRecoverAllRequest(peer)

    def ProbeFile(self,file):
        """
        Takes a file name and sends all peers storing pieces of that file
        a probe request.  
        """

        file = os.path.abspath(file)

        piecesAndPeers = self.database.GetPeersAndPiecesForFile(file)
        pair = None
        for pair in piecesAndPeers:
            (hdr, body) = dibs_msg.CreateProbeRequestHeaderAndBody(pair[0],
                                                                   pair[1])
            self.SendDataToPeer(hdr+body,pair[1])

        
        if (pair == None):
            raise DIBSException, ('No pieces and peers available for file '
                                  + file + '.\n')

        self.database.RememberAttemptingToProbeFile(file)
        
    def RespondToProbeForPeer(self,dMsg,peer):
        """
        Send piece indicated in the dMsg back to peer.
        """

        pieceName = dMsg.pieceName
        fileName = self.database.GetNameForPeerFile(dMsg.pieceName,peer)
        dibs_logger.Logger.PrintAndLog('Sending piece ' + pieceName +
                                       ' stored in file ' +
                                       fileName +
                                       ' back to peer in response to probe.\n',
                                       dibs_logger.LOG_DEBUG)

        fd = open(fileName,'rU')
        (hdr,body) = dibs_msg.CreateProbeResponseHeaderAndBody(
            pieceName,peer,fd.read())
        fd.close()

        self.SendDataToPeer(hdr + body,peer)


    def HandleProbeResponseFromPeer(self,dMsg,peer):
        """
        This function process a probe response from the peer.  Currently
        the probe message looks very similar to a recover response message.
        This function extracts the data from the message and calls the
        RememberPieceOfFileProbed to do the heavy lifting.

        Note that when we compute the hash of the message payload, we
        compute the hash of the *encrypted* payload and do *not*
        decrypt the payload.  This is because the hash stored in
        our database is a hash of the *encrypted* payload.
        """
        
        pieceName = dMsg.pieceName
        (file,pieceNum,dir,name)=self.GetRecoveryNamesAndNumbers(pieceName)
        hash = HashStringNoB2A(dMsg.payload)

        probeMatches = self.database.RememberPieceOfFileProbed(
            file,pieceNum,pieceName,hash)

        if (not probeMatches):
            # The following line tends to fill up the logfile to fast
            dibs_logger.Logger.PrintAndLog(
                'in probing piece:\n' + pieceName + '\ngot failed match\n' +
                dMsg.payload,dibs_logger.LOG_DEBUG)


    def __init__(self,database):
        """
        Initialize DIBS object. 
        """

        self.CmdHandler = {
            dibs_constants.forgetYouCmdName : 'UpdatePeerForgettingUs',
            dibs_constants.clearCmdName : 'ClearDBForPeer',
            dibs_constants.storeCmdName : 'StoreFileForPeer', 
            dibs_constants.probeCmdName : 'RespondToProbeForPeer',
            dibs_constants.probeResponseCmdName :
            'HandleProbeResponseFromPeer',
            dibs_constants.unstoreCmdName : 'UnstoreFileForPeer',
            dibs_constants.recoverCmdName : 'RecoverFileForPeer',
            dibs_constants.recoverResponseCmdName :
            'HandleRecoverResponseFromPeer',
            dibs_constants.recoverAllCmdName : 'RecoverAllForPeer',
            dibs_constants.doneRecoverAllCmdName :
            'HandleRecoverAllFinishedFromPeer',
            dibs_constants.proposalCmdName : 'HandlePeerContractProposal',
            dibs_constants.proposalResponseCmdName :
            'HandlePeerProposalResponse'
            }
        
        self.database = database

    def SendMessage(self,file,peer):
        """
        Take a full message in file and try to send it to peer.  If
        we are unable to deliver and the message is too old send a
        complaint via email.

        This function differs from the SendDataToPeer in that
        SendMessage is designed to deliver an existing file using
        either active or passive mode.  SendDataToPeer takes a
        message, creates the appropriate file and arranges for the
        message to be delivered appropriately.  Developers who want
        a message delivered should probably use SendDataToPeer and
        the only caller of SendMessage should be SendMessageCmd.
        """
        (host,port,talk) = self.database.GetCommunicationPrefsForPeer(peer)
        if (talk == 'active'):
            c = dibs_daemon.DIBSClient(peer,host,port)
            if (c.Ok()):
                c.TransmitGive([file])
        elif (talk != 'passive'):
            raise DIBSException, ('Can not send_message "' + file +
                                  '" to ' + peer + ' with talk type ' + talk)
        self.ComplainIfMessageTooOld(file)

    def SendOutgoingMessages(self):
        """
        Go through outgoing directories for each peer and send off
        any messages we can.
        """
        
        topDir = dibs_options.outgoingQueueDir
        for subdir in os.listdir(topDir):
            dibs_logger.Logger.PrintAndLog(
                'Looking in ' + subdir + ' for outgoing messages.\n',
                dibs_logger.LOG_DEBUG)

            if (self.database.PeerKnownP(subdir)):
                fullSubdir = PathJoin(topDir,subdir)
                (host,port,
                 talk) = self.database.GetCommunicationPrefsForPeer(subdir)
                if (talk == 'active'):
                    c = dibs_daemon.DIBSClient(subdir,host,port)
                    if (c.Ok()):
                        files = []
                        for file in os.listdir(fullSubdir):
                            files.append(PathJoin(fullSubdir,file))
                        if (len(files) > 0):
                            c.TransmitGive(files)
                else:
                    dibs_logger.Logger.PrintAndLog(
                        'Not sending messages in \n' + `fullSubdir` +
                        '\nbecause talk mode is ' + `talk` + '.',
                        dibs_logger.LOG_DEBUG)
                    
                    
            else:
                dibs_logger.Logger.PrintAndLog(
                    'WARNING: Directory ' + subdir +
                    ' not associated with any peers.',dibs_logger.LOG_WARNING)
                
                


    def ComplainIfMessageTooOld(self,file):
        diff = time.time() - GetModTime(file)
        if (diff > dibs_options.maxMsgAge):
            raise DIBSException, ('Could not deliver msg ' + file +
                                  ' after ' + `float(diff)/float(86400)` +
                                  ' days.')

    def ProcessMessage(self,msgFile):
        """
        Take a full mail message as input, veryify the signature, and take
        the appropriate action such as storing the file, answering the probe,
        etc.
        """

        dibsM = dibs_msg.DIBSMsg(msgFile)
            
        # The following line tends to fill up the logfile to fast
        #dibs_logger.Logger.PrintAndLog('parsed msg ' + dibsM.__str__(),
        #                               dibs_logger.LOG_DEBUG)

        if (dibsM.args.has_key(dibs_constants.publicKeyNameArgName) and
            dibsM.args.has_key(dibs_constants.publicKeyArgName)):
            dibs_crypto.ImportPublicKeyIfNecessary(
                dibsM.args[dibs_constants.publicKeyNameArgName],
                dibsM.args[dibs_constants.publicKeyArgName])

        dibsSender = self.GetDIBSSender(msgFile)
        cmdString = ('self.' + self.CmdHandler[dibsM.cmd] +
                     '(dibsM,dibsSender)')
        dibs_logger.Logger.PrintAndLog('In ProcessMessage executing: ' +
                                       cmdString,dibs_logger.LOG_DEBUG)
        eval(cmdString)


    def RecoverFile(self,file):
        """
        Takes a file name which we are storing remotely and
        asks any peers storing it to send us the stored pieces.
        Also makes an entry in the recovery database so that
        once all pieces have been received the file will be
        automatically recovered.
        """

        file = os.path.abspath(file)
        
        piecesAndPeers = self.database.GetPeersAndPiecesForFile(file)
        pair = None
        for pair in piecesAndPeers:
            (hdr, body) = dibs_msg.CreateRecoverRequestHeaderAndBody(
                pair[0],pair[1])
            self.SendDataToPeer(hdr+body,pair[1])
        if (pair == None):
            raise DIBSException, ('No pieces and peers available for file '
                                  + file + '.\n')
        (file,pieceNum,dir,name) = self.GetRecoveryNamesAndNumbers(pair[0])
        dibs_logger.Logger.PrintAndLog('Using dir ' + dir + ' for recovery.',
                                       dibs_logger.LOG_DEBUG)
        if (not os.path.exists(dir)):
            os.makedirs(dir)
        self.database.RememberAttemptingToRecoverFile(file)
        dibs_logger.Logger.PrintAndLog('Starting recovery of file '
                                       + `file` + '.',
                                       dibs_logger.LOG_DEBUG,
                                       dibs_logger.LOG_INFO)

    def RecoverAll(self):
        """
        Asks all peers to send us back any pieces they are storing.

        First we send recover all requests to every peer.
        Then we make an entry in the database for every peer
        saying that we are in recover all mode.  The peers
        should start sending back what they are storing for us.
        When we get the first piece for a file we should create
        a recovery directory for that file and follow the usual
        recovery process.  Once a peer has finished sending us
        all the pieces it is storing for us then it will send us
        a recover all finished message so that we stop waiting
        for data from that peer.  Thus once all the peers have
        finished sending us their data we will know that recovery
        is complete.
        """

        for peer in self.database.GetPeers():
            (hdr,body) = dibs_msg.CreateRecoverAllRequestHdrAndBdy(peer)
            self.SendDataToPeer(hdr+body,peer)

        self.database.RememberRecoverAllRequest()
        dibs_logger.Logger.PrintAndLog('Starting recover all.\n',
                                       dibs_logger.LOG_DEBUG,
                                       dibs_logger.LOG_INFO)

    def HandleDoneRecoverResponse(self,dMsg,peer):
        self.database.PeerDoneRespondingToRecoverAllRequest(peer)

    def FinishRecoveryByCombiningPieces(self,file):
        dir = self.database.GetNameForRecoveryDir()
        location = PathJoin(dir,file)
        fileList = self.database.GetNamesOfRecoveryPieces(file)
        for i in range(len(fileList)):
            fileList[i] = PathJoin(dir,fileList[i])
        file_ecc.DecodeFiles(fileList,location)
        for item in fileList:
            os.remove(item)
        if (dibs_options.mailUserOnRecovery and
            not self.database.DoingRecoverAllP()):
            self.MailUserThatRecoveryFinished(file,location)

        self.database.CompleteRecoveryRequest(file)

    def MailUserThatRecoveryFinished(self,file,location):
        hdr = string.join(['Subject: ','<DIBS> DIBS RECOVERED FILE ',
                           file,'\n\n'],'')
        body = string.join(['DIBS RECOVERED FILE ',file,'.\n',
                            'Recovered file at ',location,'.\n'],'')
        MailDataToUser(hdr+body,dibs_options.dibsAdmin,dibs_options.dibsAdmin,
                       dibs_options.smtpServer)

    def MailUserThatRecoverAllFinished(self):
        body = 'DIBS RECOVER ALL COMPLETED.\n'
        hdr = string.join(['Subject: ',body,'\n'],'')
        MailDataToUser(hdr+body,dibs_options.dibsAdmin,dibs_options.dibsAdmin,
                       dibs_options.smtpServer)

    def MailUserAboutProposalResponse(self,response,contractName,peer,comment):
        subject = 'DIBS RECEIVED PROPOSAL RESPONSE:' 
        body = (subject + '\n\n' +
                '\n\tPEER: ' + `peer` +
                '\n\tCONTRACT: ' + `contractName` +             
                '\n\tRESPONSE: ' + `response` +
                '\n\tCOMMENT: ' + `comment` + '\n\n')
                
        MailDataToUser('Subject: ' + subject + '\n\n' + body,
                       dibs_options.dibsAdmin,
                       dibs_options.dibsAdmin,dibs_options.smtpServer)
            
    def ClearDB(self):
        """
        Tell all our peers to forget what they are storing for us.
        Note that we forget what peers are storing for us, but still
        remember what we are storing for them.
        """

        for peer in self.database.GetPeers():
            (hdr, body) = dibs_msg.CreateClearDBHeaderAndBody(peer)
            self.SendDataToPeer(hdr+body,peer)
            
        self.database.ClearLocalDB()
        dibs_logger.Logger.PrintAndLog('\nCleared DB.\n',
                                       dibs_logger.LOG_DEBUG,
                                       dibs_logger.LOG_INFO)        

    def ForgetPeer(self,peer):
        """
        Send a message to peer saying that we forgot his data.
        Also, erase all the files we are storing for peer.
        """

        (hdr,body) = dibs_msg.CreateForgetYouMsg(peer)
        self.SendDataToPeer(hdr+body, peer)
        self.database.ForgetPeersPieces(peer)
    
        dibs_logger.Logger.PrintAndLog('\nForgot storage for peer '
                                       + peer + '.\n',
                                       dibs_logger.LOG_DEBUG,
                                       dibs_logger.LOG_INFO)
        
    def UnstoreFile(self,file):
        """
        Takes a file name which we are storing, removes it from
        our storage database and asks any peers storing it to do
        likewise.
        """

        file = os.path.abspath(file)
        piecesAndPeers = self.database.UnstorePiecesForFile(file)
        for pair in piecesAndPeers:
            (hdr, body) = dibs_msg.CreateUnstoreHeaderAndBody(pair[0],pair[1])
            self.SendDataToPeer(hdr+body,pair[1])

        # Remove probe attempt from database so that pending probes
        # do not get confused because the file is unstored.
        if (self.database.probeDatabase.has_key(file)):
            del self.database.probeDatabase[file]

        dibs_logger.Logger.PrintAndLog('Unstored file ' + file + '.',
                                       dibs_logger.LOG_DEBUG,
                                       dibs_logger.LOG_INFO)
                
    def StoreAsNecessary(self,file,storageName):
        """
        If file names a directory then all files and directories under
        this directory are stored with root given by storageName.

        Otherwise, if file is not a directory, it is stored under the
        name storageName.  If file is already stored under this name,
        and file has changed, then it is unstored and restored.
        Otherwise if file is stored and unchanged, nothing happens.
        
        If storageName is not a valid dibs file name, then a warning
        is generated and the name is transformed into a valid file
        name.

        """
        file = dibs_link.GetRealFilename(file)
        storageName = dibs_link.StripShortcutExtensionOnWindows(storageName)
        assert (file and storageName)
        if (self.ComplainIfBadFile(file)):
            return 0
            
        if (os.path.isdir(file)):
            pendingMsgs = 0
            for item in os.listdir(file):
                if (pendingMsgs > dibs_options.sendMsgThreshold):
                    self.SendOutgoingMessages()
                    pendingMsgs = 0
                pendingMsgs = (pendingMsgs +
                               self.StoreAsNecessary(PathJoin(file,item),
                                                     PathJoin(storageName,
                                                                  item)))
            return pendingMsgs

        ### The following code is only if file is actually a file not a dir.
        
        if (not self.ValidDIBSFileNameP(storageName)):
            storageName = self.TransformToValidDIBSFileName(storageName)

        if (not (self.FileBackedUpP(storageName))):
            dibs_logger.Logger.PrintAndLog('Storing file ' +
                                           file + ' as ' + storageName,
                                           dibs_logger.LOG_DEBUG)
            self.StoreFile(file,storageName)
            return 1
        elif (not self.FileSameAsStored(file,storageName)):
            dibs_logger.Logger.PrintAndLog('Unstoring file ' + storageName
                                           + ' to update with newer vesion.',
                                           dibs_logger.LOG_DEBUG)
            self.UnstoreFile(storageName)
            dibs_logger.Logger.PrintAndLog('Waiting for unstore to finish.',
                                           dibs_logger.LOG_DEBUG)
            time.sleep(dibs_options.sleepTime)
            dibs_logger.Logger.PrintAndLog('Storing file ' +
                                           file + ' as ' + storageName,
                                           dibs_logger.LOG_DEBUG)
            self.StoreFile(file,storageName)
            return 1
        else:
            dibs_logger.Logger.PrintAndLog('File ' + file +
                                           ' unchanged so not restoring.',
                                           dibs_logger.LOG_DEBUG)
            return 0

    def ComplainIfBadFile(self,file):
        """
        Check if file exists, we have permission to read it, etc.
        If there is a problem, log a warning message, and return 1.
        Otherwise return 0.
        """
        if (not os.access(file,os.R_OK)):
            dibs_logger.Logger.PrintAndLog(
                'WARNING: Unable to read file or directory "' + file +
                '" in store attempt.\n' + 'File or directory not stored.\n',
                dibs_logger.LOG_WARNING)
            return 1
        else:
            return 0
            

    def StoreFile(self,file,storageName):
        """
        Takes a file, splits into pieces, encrypts it, places
        messages in outgoing queues to request peers to store 
        the various pieces and puts the result into the store
        database under the name storageName.  Returns the
        number of pieces generated.

        After finishing, this file writes the database to disk so
        that if an error occurs in a long string of stores, we won't
        forget the ones that were processed succesfully.

        Note: This function is only meant to be called by
              StoreAsNecessary and should never be called directly.

        TODO: An exception occuring in this function can cause problems.
              The issue is that we first tell the database to remember
              that we are storing a file and then chop it into pieces,
              encode the pieces, send the pieces out, etc.  Thus if
              an exception occurs half way though, the database thinks
              we have stored the file but we really haven't.  I think
              this caused some RemoteFileNonExistent errors in versions
              prior to 0.91.  Starting with version 0.91, if an exception
              occurs we try to unstore all the pieces stored prior to
              the exception.  This should work, although it's slightly
              non-ideal since we send store requests immediately followed
              by unstore requests to the peers.
        """
        completedRequests = []
        fileSize = os.path.getsize(file)

        (N,K) = self.GetSplitParamsForFile(fileSize)
        self.database.RememberStoreFileRequest(storageName,
                                               (N,K),HashFile(file))
        try:
            tempFilePrefix = tempfile.mktemp()
            fileList = file_ecc.EncodeFile(file,tempFilePrefix,N,K)
            assert len(fileList) == N
        
            for i in range(N):
                fd = open(fileList[i], 'rU')
                data = fd.read()
                fd.close()
                os.remove(fileList[i])
                storeData = self.StorePiece(storageName,data,i)
                completedRequests.append(storeData)
            assert len(self.database.peerDatabase) > 0
            self.database.SaveToFile(dibs_options.databaseFilePrefix)
        except Exception, e:
            dibs_logger.Logger.PrintAndLog(
                'Could not store file ' + `file` + ' using name ' +
                `storageName` + '\n due to exception: ' + `e`,
                dibs_logger.LOG_CRITICAL)
            self.UnstoreFile(storageName)
            raise e
        return N

    def GetSplitParamsForFile(self,fileSize):
        K = int(min(256 - dibs_options.redundantPieces,
                    max(1,math.ceil(float(fileSize)/dibs_options.kbPerFile
                                    /1000))))
        N = K + dibs_options.redundantPieces
        return (N,K)

    def StorePiece(self,file,data,pieceNumber):
        """
        Take a single piece of a file generate a name for it,
        encrypt it, store it and return a tuple containing
        (file,pieceName,peer,path) where file is the name of
        the file we stored, pieceName is the name we stored it as,
        and peer is the peer we stored it with.
        """

        pieceName = self.GenerateNameForPiece(file,pieceNumber)
        encryptedPiece = dibs_crypto.EncryptPiece(
            data,dibs_options.dibsPrivateKey)
        peer = self.database.FindPeerToStorePiece(len(encryptedPiece)+2000)
        (hdr, body) = dibs_msg.CreateStoreHeaderAndBody(peer,encryptedPiece,
                                                        pieceName)
        self.StoreInOutgoingQ(hdr+body,peer)
        payload = encryptedPiece
        self.database.RememberStorePieceRequest(file,payload,pieceName,peer)
        return (file,pieceName,peer)

    def ValidDIBSFileNameP(self,fileName):
        """
        Returns true if fileName does not contain a forbiden sequence
        (e.g., the separator used to separate a file from a piece.)
        """
        return not string.count(fileName,dibs_constants.fileSeparator)

    def TransformToValidDIBSFileName(self,name):
        rep = string.replace(name,dibs_constants.fileSeparator,
                             dibs_constants.transSep)
        dibs_logger.Logger.PrintAndLog('WARNING: Storing file ' + name +
                                       ' as ' + rep,dibs_logger.LOG_WARNING)
        return rep
        
    def GenerateNameForPiece(self,file,pieceNumber):
        """
        Generate a unique name for the piece of file.
        """

        clearName = string.join([file,dibs_constants.fileSeparator,
                                 string.zfill(`pieceNumber`,7)],'')
        return dibs_crypto.EncryptToSelf(clearName)

    def SendDataToPeer(self,data,peer,host=None,port=None,talk=None):
        """
        Puts message in outgoing queue and delivers the message
        using the talk method specified for peer.  Usually, the
        optional arguments host, port, and talk should *not* be
        provided since they will be obtained automatically from
        the database.  One exception is when peers are trying
        to agree/propose on contracts and they might not be in
        the database.
        """

        path = self.StoreInOutgoingQ(data,peer)

        if (host == None): 
            (host,port,talk) = self.database.GetCommunicationPrefsForPeer(peer)
            
        if (talk == 'sendmail'):
            self.MailDataToPeerViaSendmail(path,peer)
        elif (talk == 'smtplib'):
            self.MailDataToPeerViaSMTPLIB(path,peer)
        elif (talk == 'active'):
            client = dibs_daemon.DIBSClient(peer,host,port)
            if (client.Ok()):
                client.TransmitGive([path])
        elif (talk == 'passive'):
            pass
        else:
            raise DIBSException, ('Unknown talk method: ' + talk)


    def StoreInOutgoingQ(self,data,peer):
        """
        Puts message in outgoing queue and returns filename of
        message.
        """

        path = PathJoin(dibs_options.outgoingQueueDir,peer)
        if (not os.path.exists(path)):
            os.mkdir(path)
        path = (PathJoin(path,`round(time.time()*1000)`
                             + HashToFileName(data)))
        dibs_logger.Logger.PrintAndLog('Storing outgoing message in '
                                       + path + '.\n',dibs_logger.LOG_DEBUG)
        fd = open(path,'wU')
        fd.write(data)
        fd.close()

        return path

    def MailDataToPeerViaSendmail(self,file,peer):
        "Emails data to peer by looking up peer's address in database."

        emailAddress = self.database.GetAddressForPeer(peer)
        fileFD = open(file,'rU')
        
        fd = os.popen(dibs_constants.sendmailCommand + ' ' + \
                      emailAddress,'wU')
        fd.write(fileFD.read())
        fileFD.close()
        fd.close()

    def MailDataToPeerViaSMTPLIB(self,file,peer):
        "Emails data to peer by looking up peer's address in database."

        
        emailAddress = self.database.GetAddressForPeer(peer)
        fromAddr = dibs_options.dibsAdmin

        server = smtplib.SMTP(dibs_options.smtpServer)
#        server.set_debuglevel(1)
        fileFD = open(file,'rU')
        server.sendmail(fromAddr,emailAddress,fileFD.read())
        fileFD.close()

    def GetDIBSSender(self,msgFile):
        """
        Verify the digital signature from msgFile and return the
        email address of the signing key.
        """

        cmd = dibs_crypto.MakeVerifyCmd(msgFile)
        dibs_logger.Logger.PrintAndLog('Attempting to verify signature using '+
                                       cmd + '.\n',dibs_logger.LOG_DEBUG)
        (status, output) = getstatusoutput(cmd)
        if (status):
            raise BadSignature, (status,output)
        else:
            sigRE = '(?m)(?i)gpg: good signature from "'
            sigRE = sigRE + '(?P<name>[^\(]+)?'
            sigRE = sigRE + ' +(\((?P<comment>[^\)]+)\))?'
            sigRE = sigRE + ' *<(?P<email>[^>]+)> *"'
            m = re.search(sigRE,output)
            if (not m):
                errMsg = 'Unable to extract user from:\n' + output
                raise BadSignature, (0,errMsg)
            else:
                return m.group('email')

    def GetRecoveryNamesAndNumbers(self,pieceName):
        """
        Returns (fileName,pieceNum,dir,pName) where fileName is the
        name of the file being recovered of which pieceName is a part,
        pieceNum is the number corresponding to the file named pieceName,
        pName is the name of the file where the data for this piece should
        be stored in the directory dir.
        
        Note: Make sure to reflect any changes to the format for pName or
        dir into the GetNamesOfPieces function in dibs_database.py.
        """
        pieceName = dibs_crypto.DecryptFromSelf(string.strip(pieceName))
        myRE = string.join(['^(.+)',dibs_constants.fileSeparator,
                           '([0-9]+)$'],'')
        m = re.match(myRE,pieceName)
        assert m, ('GetRecoveryNamesAndNumbers: Weird file name \'' +
                   pieceName + '\' failed to match regexp \'' + myRE + '\'.')
        file = m.group(1)
        fileRoot = os.path.dirname(file)
        recoveryDir = PathJoin(self.database.GetNameForRecoveryDir(),
                               fileRoot)
        return (file,m.group(2),recoveryDir,
                os.path.basename(file + dibs_constants.fileSeparator +
                                 m.group(2)))

    def FileBackedUpP(self,file):
        return self.database.FileBackedUpP(file)

    def HashForStoredFile(self,file):
        return self.database.HashForStoredFile(file)
        
    def FileSameAsStored(self,file,stored):
        oldHash = self.HashForStoredFile(stored)
        newHash = HashFile(file)
        return oldHash == newHash

    def Cleanup(self):
        for dir in self.database.GetAllPeerDirs():
            for subDir in os.listdir(dir):
                DeleteEmptyDirs(PathJoin(dir,subDir))
        
    def PostPeerContract(self,host,port,talkType,listenType,
                         minQuota,maxQuota,quotaMultiplier,lifetime,name,url):
        """
        Post an advertisement for a contract.

        host,port:  The host and daemon port of the poster.
        talkType, listenType: The talk mode and listen mode from the
                              point of view of the poster.
        minQuota, maxQuota:   The min/max remote_quota the poster wants.
        quotaMultiplier:      The ratio of remote_quota/local_quota
                              the poster wants.
        lifetime:             How long (in seconds) the contract proposal
                              should stay active.
        name:                 name for the contract.
        url:                  url to post contract to
        """
        contract = dibs_contract.DIBSPostedContract(
            host,port,talkType,listenType,
            dibs_options.dibsPublicKey,dibs_options.dibsAdmin,
            minQuota,maxQuota,quotaMultiplier,lifetime,name)
        self.database.RememberContractPosted(contract,url)

    def UnpostPeerContract(self,contractName,url):
        self.database.ForgetPeerContract(contractName,url)

    def ProposePeerContract(self,contractName,localQuota,remoteQuota,
                            talk,listen,host,
                            peer,peerHost,peerPort,peerEmail,url):
        """
        The ProposePeerContract function proposes a contract to the peer.
        All the arguments (except peerHost, peerPort, peerEmail) are
        from the point of view of the recipient we are proposing the
        contract to.  For example, the talkType is what the peer would
        use as the argument to --talk and the remoteQuota is
        what the peer would use as the argument to --remote_quota in
        the add_peer function.
        """

        if (None == url or '' == url.strip()): # use default
            url = dibs_options.defaultContractServerURL
        if ('none' != url.lower()): # fill in info from url
            contract = dibs_contract.DIBSPostedContract(
                name=contractName,host=peerHost,port=peerPort,admin=peerEmail,
                pubKey=peer,url=url)
            (peerHost,peerPort,peerEmail,peer) = contract.GetPeerParams()
	else:
            dibs_logger.Logger.PrintAndLog('Not filling in data from URL.',
                                           dibs_logger.LOG_WARNING)
	    contract = dibs_contract.DIBSPostedContract(
                name=contractName,host=peerHost,port=peerPort,admin=peerEmail,
                pubKey=peer)
            (peerHost,peerPort,peerEmail,peer) = contract.GetPeerParams()

        dibs_logger.Logger.PrintAndLog('Posted contract data:\n' +
                                       contract.__str__(),
                                       dibs_logger.LOG_INFO)
        dibs_logger.Logger.PrintAndLog('Attempting to import key with name ' +
                                       `contract.keyNameForContract` + ':\n' +
                                       `contract.publicKey`,
                                       dibs_logger.LOG_INFO)
        dibs_crypto.ImportPublicKeyIfNecessary(contract.keyNameForContract,
                                               contract.publicKey)

        proposal = dibs_contract.DIBSProposedContract(
            contractName,localQuota,remoteQuota,talk,listen,host,
            dibs_options.daemonPort,peerHost,peerPort,peerEmail,
            dibs_options.dibsPublicKey,dibs_options.dibsAdmin)

        (hdr,body) = dibs_msg.CreatePeerProposalHeaderAndBody(
            peer,contractName,proposal.talk,proposal.listen,remoteQuota,
            localQuota,host)

        if (self.database.PeerKnownP(peer)):
            self.database.EditPeer(peerEmail,peer,None,None,None,
                                   proposal.listen,proposal.talk,
                                   peerHost,peerPort)
        else:
            self.database.AddPeer(peerEmail,peer,0,0,
                                  'temporary entry for proposal',
                                  proposal.listen,proposal.talk,
                                  peerHost,peerPort)

        self.SendDataToPeer(hdr+body,peer)

                       
        self.database.RememberContractProposed(proposal)
        
        self.database.SaveToFile(dibs_options.databaseFilePrefix)

    def CheckRQuota(self,dMsg,contract):

        rQuota = long(dMsg.args[dibs_constants.remoteQuotaArgName])
        if (rQuota < long(contract.minQuota)):
            msg = (dibs_constants.proposalErrors['remote_quota_range'] +
                   '\nproposed remote_quota = ' + `rQuota` +
                   '\nminimum contract value = ' + `contract.minQuota`)
            dibs_logger.Logger.PrintAndLog(msg,dibs_logger.LOG_WARNING)
            return (None,'NO',msg)
        elif (rQuota > long(contract.maxQuota)):
            msg = (dibs_constants.proposalErrors['remote_quota_range'] +
                   '\nproposed remote_quota = ' + `rQuota` +
                   '\nmaximum contract value = ' + `contract.maxQuota`)
            dibs_logger.Logger.PrintAndLog(msg,dibs_logger.LOG_WARNING)
            return (None,'NO',msg)
        else:
            return (rQuota,'YES','')


    def CheckLQuota(self,dMsg,contract):

        lQuota = long(dMsg.args[dibs_constants.localQuotaArgName])
        rQuota = long(dMsg.args[dibs_constants.remoteQuotaArgName])
        if (float(rQuota)/float(lQuota) < contract.quotaMultiplier):
            msg = (dibs_constants.proposalErrors['bad_quota_mult'] +
                   '\nproposed remote_quota = ' + `rQuota` +
                   '\nproposed local_quota = ' + `lQuota` +                   
                   '\nminimum contract quota_multiplier = '
                   + `contract.quotaMultiplier`)
            dibs_logger.Logger.PrintAndLog(msg,dibs_logger.LOG_WARNING)
            return (None,'NO',msg)
        else:
            return (long(lQuota),'YES','')


    def MakeProposalDecision(self,dMsg,peer,contractName,host,port):

        try:
            contract = self.database.GetContractByName(contractName)
            if (None == contract):
                return ('NO',dibs_constants.proposalErrors['unknown_contract'])

            talkType = dMsg.args[dibs_constants.talkTypeArgName]
            if ('any' != contract.peerTalkType and
                contract.peerTalkType != talkType):
                return ('NO',dibs_constants.proposalErrors['bad_talk_type'])

            listenType = dMsg.args[dibs_constants.listenTypeArgName]
            if ('any' != contract.peerListenType and
                contract.peerListenType != listenType):
                return ('NO',dibs_constants.proposalErrors['bad_listen_type'])
            
            if (not self.database.PeerKnownP(peer)):
                self.database.AddPeer(dMsg.args[dibs_constants.adminArgName],
                                      peer,0,0,
                                      'Added peer from proposal for contract '
                                      +`contract.name`,
                                      talkType,listenType,host,port)

            (rQuota, response, comment) = self.CheckRQuota(dMsg,contract)
            if (None == rQuota):
                return (response, comment)

            (lQuota, response, comment) = self.CheckLQuota(dMsg,contract)
            if (None == lQuota):
                return (response, comment)

            if (self.database.PeerKnownP(peer)):
                self.database.EditPeer(dMsg.args[dibs_constants.adminArgName],
                                       peer,rQuota,lQuota,None,
                                       talkType,listenType,
                                       host,port,addQuotas=1)

            self.database.ForgetPeerContract(contract.name,contract.url)
                
        except Exception, e:
            exc_info = sys.exc_info()
            msg = (dibs_constants.proposalErrors['exception'] +
                    '\n' + e.__str__() + '\n' +
                   GetTracebackString(exc_info))
            dibs_logger.Logger.PrintAndLog(
                'Got exception processing contract:\n' + msg,
                dibs_logger.LOG_WARNING)
            return ('NO',msg)
            
        return ('YES',' ')

    def GetEssentialProposalInfo(self,dMsg):

        
        if (dMsg.args.has_key(dibs_constants.talkTypeArgName)):
            talkType = dMsg.args[dibs_constants.talkTypeArgName]
        else:
            return ('NO',None,None,None)

        if (dMsg.args.has_key(dibs_constants.hostArgName)):
            host = dMsg.args[dibs_constants.hostArgName]
        else:
            return ('NO',talkType,None,None)            

        if (dMsg.args.has_key(dibs_constants.portArgName)):
            port = dMsg.args[dibs_constants.portArgName]
        else:
            return ('NO',talkType,host,None)

        return ('YES',talkType,host,port)
        
    def HandlePeerContractProposal(self,dMsg,peer):

        (response, talkType, host, port)=self.GetEssentialProposalInfo(dMsg)

        if ('NO' == response):
            dibs_logger.Logger.PrintAndLog(
                'Ignoring contract proposal with invalid comm info.',
                dibs_logger.LOG_WARNING)
            return

        if (dMsg.args.has_key(dibs_constants.contractNameArgName)):
            contractName = dMsg.args[dibs_constants.contractNameArgName]
            (response, comment) = self.MakeProposalDecision(
                dMsg,peer,contractName,host,port)
        else:
            response = 'NO'
            comment = dibs_constants.proposalErrors['unknown_contract']
            contractName = '<unknown>'

        (hdr, body) = dibs_msg.CreateProposalResponseHeaderAndBody(
            peer, contractName, response, comment)

        self.SendDataToPeer(hdr+body,peer,host,port,talkType)

    def HandlePeerProposalResponse(self,dMsg,peer):
        """
        The HandlePeerProposalResponse function handles the response
        to a proposed contract.  Note that most of the parameters
        in the proposal are from the point of view of the peer we
        proposed the contact to and thus the arguments to EditPeer
        may seem reversed at first glance.
        """

        response = dMsg.args[dibs_constants.proposalDecisionArgName]
        contractName = dMsg.args[dibs_constants.contractNameArgName]
        comment = dMsg.args[dibs_constants.proposalCommentArgName]
        
        proposal = self.database.RemoveProposalForContract(contractName)

        if (response == 'YES'):
            self.database.EditPeer(proposal.peerEmail,peer,
                                   proposal.localQuota,
                                   proposal.remoteQuota,
                                   'Peer accepted proposal for contract ' +
                                   contractName,proposal.listen,
                                   proposal.talk,proposal.peerHost,
                                   proposal.peerPort,addQuotas=1)
            dibs_logger.Logger.PrintAndLog(
                'Proposal for contract ' + contractName + ' accepted.\n',
                dibs_logger.LOG_INFO)
        else:
            dibs_logger.Logger.PrintAndLog(
                'Proposal for contract ' + contractName +
                ' rejected with comment ' + comment,dibs_logger.LOG_WARNING)

        self.MailUserAboutProposalResponse(response,contractName,peer,comment)
            
        
    def PrintAndLog(self,msg,logLevel=dibs_logger.LOG_INFO,printLevel=None):
        return dibs_logger.Logger.PrintAndLog(msg,logLevel,printLevel)
