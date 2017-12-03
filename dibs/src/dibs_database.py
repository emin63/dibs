import time
import string
import md5
import cPickle
import os, os.path
import random

import dibs_logger
import dibs_constants
import dibs_options
import dibs_statistics
import dibs_contract
import dibs_crypto

from dibs_utils import *
from dibs_exceptions import *

import ffield, ffield.file_ecc

class PeerStorageRecord:
    """
    This class implements records to track how much stuff
    peers are storing, as well as their email address
    probe history, reliability, quota, and storage with us.

    Note that we consider the peer to be the ``email'' address
    of the cryptographic key we use to communicate with someone.
    The true email adddress is simply a property of the peer.
    This is done so that the same user (and the same email address)
    can have multiple dibs identities.

    email is the address we send mail to for peer.
    remoteQuota is how much room we can use on the peer.
    remoteStorage is how much space we are using on the peer.
    localQuota is how much space the peer can use on us.
    localStorage is how much space the peer is using on us.
    storedData is a dictionary containing names of files we are storing
       for peer with the corresponding times the store requests were sent.

    Note all sizes for quotas and storage are in bytes even though the
    user specifies values for the add_peer command in kilo-bytes (i.e.,
    add_peer command multiplies the user's value by 1000).
    """
    
    def __init__(self,email,remoteQuota,localQuota,comment,
                 talk,listen,host,port):
        self.email = email
        self.remoteQuota = remoteQuota
        self.remoteStorage = 0
        self.localQuota = localQuota
        self.localStorage = 0
        self.storedData = {}
        self.comment = comment
        self.talk = talk
        self.listen = listen
        self.host = host
        self.port = port
        if (not self.port):
            self.port = dibs_constants.defaultPort

    def ShowInfo(self):
        msg = '{'
        for item in ('email','comment','talk','listen','host','port'):
            msg = msg + '\n\t' + item + '=' + `eval('self.' + item)` + ','
        for item in ('remoteQuota','remoteStorage',
                     'localQuota','localStorage'):
            msg = (msg + '\n\t' + item + '=' + `eval('self.' + item)` +
                   ' (bytes),')
        msg = msg + '\n}'
        return msg
            
    def __str__(self):
        msg = '{'
        for item in ('email','comment','talk','listen','host','port'):
            msg = msg + '\n\t' + item + '=' + `eval('self.' + item)` + ','
        for item in ('remoteQuota','remoteStorage',
                     'localQuota','localStorage'):
            msg = (msg + '\n\t' + item + '=' + `eval('self.' + item)` +
                   ' (bytes),')
        msg = msg + '\n\t{STORED_DATA = '
        for k in self.storedData.keys():
            msg = msg + '\n  key:"' + k + '"\n  value:  ' + self.storedData[k]
        msg = msg + '\n}'
        return msg

    def RemainingRemoteStorage(self):
        return self.remoteQuota - self.remoteStorage

    def ModifyRemoteStorage(self,num):
        self.remoteStorage = self.remoteStorage + num

    def ZeroRemoteStorage(self):
        self.remoteStorage = 0

    def ModifyLocalStorage(self,num):
        self.localStorage = self.localStorage + num

class PieceStorageRecord:
    "This class implements a record to track storage of a piece."
    
    def __init__(self,piece,peer):
        """
        Record that we asked peer to store piece.

        Note that we currently store the hash of the piece *after*
        the piece is encrypted.
        """
        
        self.pieceHash = HashStringNoB2A(piece)
        self.size = len(piece)
        self.peer = peer
        self.status = 'STORED'
        
    def __str__(self):
        msg = ('{ {HASH(base64)=' + binascii.b2a_base64(self.pieceHash)
               + '}, PEER = "' + self.peer + '", STATUS = '
               + self.status + '}')
        return msg
        
    def GetPeerStoringPiece(self):
        return self.peer

    def MarkAsLost(self):
        self.status = 'LOST'

    def StoredP(self):
        return self.status == 'STORED'

    def GetPeer(self):
        return self.peer

    def GetHash(self):
        return self.pieceHash

class FileStorageRecord:
    "This class implements a record to track storage of a file."
        
    def __init__(self,fileName,storageCode,hash):
        """
        fileName = name of file we are storing.
        storageCode = (N,K) where N and K are parameters of the RS code used.
        hash = MD5 hash of file.
        """
        self.fileName = fileName
        self.storageCode = storageCode
        self.hash = hash
        self.pieces = {}

    def __str__(self):
        msg = string.join(['{STORED_FILE = ',self.fileName,', STORAGE_CODE = ',
                           `self.storageCode`,', HASH = ',self.hash,
                           ', NUM_PIECES = ',`len(self.pieces)`,' \n'],'')
        for key in self.pieces.keys():
            msg = msg + '\t{PIECES =' + key + ','
            msg = msg + self.pieces[key].__str__() + '}\n'
        return msg + '}'

    def AddPieceStoreRequest(self,pieceName,piece,peer):
        """
        Update the file record to record that we asked peer to
        store the piece named pieceName.
        
        Note this should only be called by RememberStoreRequest.
        """
        
        if (not self.pieces.has_key(pieceName)):
            self.pieces[pieceName] = PieceStorageRecord(piece,peer)

        return self.pieces[pieceName]

    def MarkPiecesFromPeerAsLost(self,peer):
        lost = []
        for pieceName in self.pieces.keys():
            pieceRecord = self.pieces[pieceName]
            if (peer == pieceRecord.GetPeer()):
                pieceRecord.MarkAsLost()
                lost.append((peer,pieceRecord.size))
        return lost

    def GetMinPiecesNeededForRecovery(self):
        return self.storageCode[1]

class RecoveryAttempt:
    """
    This class keeps track of the pieces of a file we are trying to recover.
    """

    def __init__(self,fName,pToRec):
        self.fileName = fName
        self.piecesToRecover = pToRec
        self.startEpoch = time.time()
        self.piecesRecovered = {}

    def __str__(self):
        return string.join(['{FILE_TO_RECOVER ',self.fileName,', START_TIME ',
                            `self.startEpoch`,' PIECES_TO_RECOVER ',
                            `self.piecesToRecover`,' PIECES_RECOVERED ',
                            `self.piecesRecovered.keys()`],'')

    def RememberPieceRecovered(self,pieceNumber):
        self.piecesRecovered[pieceNumber] = 1

    def RecoveredEnoughPieces(self):
        return len(self.piecesRecovered) >= self.piecesToRecover

    def GetNamesOfPieces(self):
        """
        Return a list of file names for the recovered pieces.
        Note that the GetRecoveryNamesAndNumbers determines what
        file names these pieces were given when stored.

        Note, only file names (without directory info) are returned.
        """
        assert self.RecoveredEnoughPieces()
        result = []
        base = self.fileName + dibs_constants.fileSeparator 
        for p in self.piecesRecovered.keys():
            result.append(base + p)
        return result

    def PartiallyEmpty(self):
        """
        Returns true if the recovery record is partially empty since
        it was created during a recover all attempt.
        """
        return None==self.piecesToRecover

    def CompletePartiallyEmptyRecordFromPiece(self,fname):

        fileInfo = ffield.file_ecc.ParseHeaderFromFile(fname)
        self.piecesToRecover = int(fileInfo['k'])

class ProbeAttempt:
    """
    This class keeps track of a probe request for a file.
    """

    def __init__(self,fName,numPToRec,peersAndPieces):
        self.fileName = fName
        self.piecesToRecover = numPToRec
        self.startEpoch = time.time()
        self.peersForUnprobedPieces = {}
        self.probeResultForPieceName = {}

        for pair in peersAndPieces:
            self.peersForUnprobedPieces[pair[0]] = pair[1]

    def __str__(self):
        return string.join(['{\n\tFILE_TO_PROBE ',self.fileName,
                            ',\n\tSTART_TIME ',
                            `self.startEpoch`,
                            ',\n\tPIECES_NEEDED_FOR_RECOVERY ',
                            `self.piecesToRecover`,
                            ',\n\tRESULTS_FOR_PIECES_PROBED ',
                            `self.probeResultForPieceName.values()`,
                            ',\n\tPEERS_WITH_UNPROBED_PIECES ',
                            `self.peersForUnprobedPieces.values()`,'\n}'],'')

    def RememberPieceProbed(self,pieceNumber,pieceName,probeResult):
        peer = self.peersForUnprobedPieces[pieceName]
        self.probeResultForPieceName[pieceName] = (probeResult, peer,
                                                   time.time()-self.startEpoch)
        del self.peersForUnprobedPieces[pieceName]

    def ProbedEnoughPieces(self):
        return len(self.piecesRecovered) >= self.piecesToRecover

    def ProbeCompletedP(self):
        return (0 == len(self.peersForUnprobedPieces))

    def RecordProbeStats(self,database):
        for pieceName in self.probeResultForPieceName.keys():
            result = self.probeResultForPieceName[pieceName]
            if (1 == result[0]):
                database.statsDatabase.RecordProbeGood(result[1],result[2])
            else:
                assert 0 == result[0]
                database.statsDatabase.RecordProbeFailed(result[1])
        for pieceName in self.peersForUnprobedPieces:
            database.statsDatabase.RecordProbeTimeout(
                self.peersForUnprobedPieces[pieceName])

    def TooOldP(self):
        return (time.time() - self.startEpoch >= dibs_options.probeTimeout)

class DIBSDatabase:
    """
    This class implements a database to keep track of who is storing what.

    The basic idea is that the DIBSDatabase has a dictionary of
    FileStorageRecord objects and PeerStorageRecord objects.  Each
    FileStorageRecord object contains a dictionary of
    PieceStorageRecord objects which remembers who stores which piece.
    To remember a store request, we get the file record for the piece,
    get the piece record, and note which peer we stored with.

    The PeerStorageRecord objects keep track of the 
    storage at each peer, as well as probe history, reliability, etc.

    TODO:
    
    This class could probably be significantly improved using a
    real relational database since the PeerStorageRecord 
    and FileStorageRecord objects could get out of sync in our
    current implementation.  Then again, using something like MySQL,
    Postgres, or Oracle will probably add too much overhead.  It
    should be possible to cobble more relational database (at least
    for a single table) into python.  
    """

    def __init__(self):
       "Initialize the storage database to be empty."

       self.fileDatabase = {}
       self.peerDatabase = {}
       self.recoveryDatabase = {}
       self.probeDatabase = {}
       self.sortedPeerList = []
       self.peersRespondingToRecoverAll = {}
       self.statsDatabase = dibs_statistics.DIBSStatDatabase()
       self.postedContractDatabase = {}
       self.proposedContractDatabase = {}       

    def __str__(self):
        return ('{\nstatsDatabase = ' + self.statsDatabase.Show() +
                self.ShowPostedContractDatabase() +
                self.ShowProposedContractDatabase() +
                'fileDatabase = ' + self.ShowFileDatabase() +
                'peerDatabase = ' + self.ShowPeerDatabase() +
                'recoveryDatabase = ' + self.ShowRecoveryDatabase() +
                'probeDatabase = ' + self.ShowProbeDatabase() +
                'SORTED_PEERS = ' + `self.sortedPeerList` + '\n')
        return msg + '}\n'

    def ShowStorage(self):
        msg = '{\n'
        for peer in self.peerDatabase.keys():
            rec = self.peerDatabase[peer]
            msg = (msg + '\t' + peer + '\t{'
                   + '\n\t\tremote_quota = ' + `rec.remoteQuota` 
                   + '\n\t\tremote_storage = ' + `rec.remoteStorage`
                   + '\n\t\tlocal_quota = ' + `rec.localQuota` 
                   + '\n\t\tlocal_storage = ' + `rec.localStorage` + '\n\t}\n')
        return msg + '}\n'

    def ShowPostedContractDatabase(self):
        return (string.join(['\n<POSTED_CONTRACT_DB>'] +
                            map(lambda x: x.__str__(),
                                self.postedContractDatabase.values()),'\n') +
                '</POSTED_CONTRACT_DB>\n')
    
    def ShowProposedContractDatabase(self):
        return (string.join(['\n<PROPOSED_CONTRACT_DB>'] +
                            map(lambda x: x.__str__(),
                                self.proposedContractDatabase.values()),'\n') +
                '</PROPOSED_CONTRACT_DB>\n')    

    def ShowFileDatabase(self):
        msg = '{\n'
        for key in self.fileDatabase.keys():
            msg = msg + '{' + key + ', ' + self.fileDatabase[key].__str__()
            msg = msg + '}'
        return msg + '}\n\n'

    def ShowFileDatabaseKeys(self):
        return string.join(self.fileDatabase.keys(),'\n')

    def ShowPeerDatabase(self):
        msg = '{\n'
        for key in self.peerDatabase.keys():
            msg = msg + '{' + key + ', ' + self.peerDatabase[key].__str__()
            msg = msg + '}\n'
        msg = msg + '}\n\n'
        return msg

    def ShowPeerInfo(self):
        msg = '{\n'
        for key in self.peerDatabase.keys():
            msg = msg + '{' + key + ', ' + self.peerDatabase[key].ShowInfo()
            msg = msg + '}\n'
        msg = msg + '}\n\n'
        return msg


    def ShowProbeDatabase(self):
        msg = '{\n'
        for key in self.probeDatabase.keys():
            msg = msg + '{' + key + ', ' + self.probeDatabase[key].__str__()
            msg = msg + '}\n'
        msg = msg + '}\n\n'
        return msg

    def ShowRecoveryDatabase(self):
        msg = '{\n'
        for key in self.recoveryDatabase.keys():
            msg = msg + '{' + key + ', ' + self.recoveryDatabase[key].__str__()
            msg = msg + '}\n'
        msg = msg + '}\n\n'
        return msg

    def GetPassivePeers(self):
        """
        Return a list of peers who expect us to contact them to get
        our messages.
        """
        
        passivePeers = filter(lambda x: self.peerDatabase[x].listen=='passive',
                              self.peerDatabase.keys())
        return map(lambda p: (p,self.peerDatabase[p]),passivePeers)

    def SaveToFile(self,filePrefix):
        """
        Saves the various DIBS databases to files.

        First, we save a database to <fileName>.CRASH and then move
        each of thoseo <fileName>.  This should help in recovering
        from situations where the machine crashes while writing the
        database to disk.
        """

        for item in ['statsDatabase', 'fileDatabase',
                     'postedContractDatabase', 'proposedContractDatabase',
                     'peerDatabase', 'recoveryDatabase', 'probeDatabase',
                     'sortedPeerList','peersRespondingToRecoverAll']:
            fileName = filePrefix + '.' + item + '.CRASH'
            fd = open(fileName,'wb')
            cPickle.dump(self.__dict__[item],fd)
            fd.close()

        for item in ['statsDatabase', 'fileDatabase',
                     'postedContractDatabase', 'proposedContractDatabase',
                     'peerDatabase', 'recoveryDatabase', 'probeDatabase',
                     'sortedPeerList','peersRespondingToRecoverAll']:
            fileName = filePrefix + '.' + item
            if (os.path.exists(fileName)):
                os.remove(fileName)
            os.rename(fileName + '.CRASH', fileName)

        dibs_logger.Logger.PrintAndLog('Saved database with prefix ' +
                                       filePrefix + '.',
                                       dibs_logger.LOG_DEBUG) 

    def GenericDBLoadMethod(self,filePrefix,item):
        fileName = filePrefix + '.' + item
        if (os.path.exists(fileName)):
            fd = open(fileName,'rb')
            self.__dict__[item] = cPickle.load(fd)
            fd.close()
        else:
            dibs_logger.Logger.PrintAndLog(
                'WARNING: file ' + `fileName` +
                ' does not exist.  Using empty database.\n',
                dibs_logger.LOG_WARNING)
            fd = open(fileName,'wb')
            cPickle.dump(self.__dict__[item],fd)
            fd.close()
            
    
    def LoadFromFile(self,filePrefix):

        for nameMethodPair in map(None,[
            'statsDatabase',
            'postedContractDatabase', 'proposedContractDatabase',
            'fileDatabase','peerDatabase','recoveryDatabase',
            'probeDatabase','sortedPeerList','peersRespondingToRecoverAll'],
                                  [self.GenericDBLoadMethod]*9):
            nameMethodPair[1](filePrefix,nameMethodPair[0])

    def ImportStatDBFromFile(self,fileName):
        ok = self.statsDatabase.ImportFromFile(fileName)
        if (not ok):
            dibs_logger.Logger.PrintAndLog(
                'WARNING: file ' + `fileName` + 'not a valid stats database.',
                dibs_logger.LOG_WARNING)

    def RememberStoreFileRequest(self,file,(N,K),hash):
        """
        Make an entry in the database noting that we are storing file
        which is broken up using an (N,K) RS code and the given hash.
        """
        if (self.fileDatabase.has_key(file)):
            raise DuplicateStoreFileRequest, file
        
        self.fileDatabase[file] = FileStorageRecord(file,(N,K),hash)

    def RememberStorePieceRequest(self,file,piece,pieceName,peer):
        """
        Put parameters of store request into database.
        """
        pieceStorageRec = self.fileDatabase[file].AddPieceStoreRequest(
            pieceName,piece,peer)

        peerRecord = self.peerDatabase[peer]
        peerRecord.ModifyRemoteStorage(pieceStorageRec.size)

    def RemainingQuotaForPeerOnOurMachine(self,peer):
        """
        Get the number of bytes peer has left which he can store on
        our machine.
        """

        peerRecord = self.peerDatabase[peer]
        return peerRecord.localQuota - peerRecord.localStorage

    def StorageForPeerOnOurMachine(self,peer):
        """
        Get the number of bytes peer is storing on our machine.
        """

        peerRecord = self.peerDatabase[peer]
        return peerRecord.localStorage

    def RememberStoringPieceForPeerOnOurMachine(self,dibsMsg,peer):
        """
        Remember that we are storing a piece for peer.
        """
        
        peerRecord = self.peerDatabase[peer]

        if (peerRecord.storedData.has_key(dibsMsg.pieceName)):
            raise DuplicateStorageRequestFromPeer, dibsMsg
        else:
            peerRecord.storedData[dibsMsg.pieceName] = dibsMsg.cmdTime
            peerRecord.ModifyLocalStorage(len(dibsMsg.payload))

        
    def QuotaForPeer(self,peer):
        peerRecord = self.peerDatabase[peer]
        return (peerRecord.localQuota,peerRecord.localStorage)

    def AddPeer(self,email,peer,remoteQuota,localQuota,comment,
                talk,listen,host,port):
        assert not self.peerDatabase.has_key(peer), 'Peer already present.'
        
        self.peerDatabase[peer] = PeerStorageRecord(email,remoteQuota,\
                                                    localQuota,comment,
                                                    talk,listen,host,port)
        self.ResortPeers()
        peerDirName = self.GetNameForPeerDir(peer)
        if (os.path.exists(peerDirName)):
            if (len(os.listdir(peerDirName)) > 0):
                # complain about non empty peer dir that already exists
                raise PeerDirExistsException(peerDirName,peer)
            else:
                pass # empty directory exists so don't worry about it
        else:
            os.mkdir(self.GetNameForPeerDir(peer))

    def EditPeer(self,email,peer,remoteQuota,localQuota,comment,
                 talk,listen,host,port,addQuotas=0):
        self.ComplainIfNoSuchPeer(peer)
        peerRecord = self.peerDatabase[peer]
        if (None != remoteQuota):
            if (addQuotas):
                remoteQuota += peerRecord.remoteQuota
            elif (remoteQuota < peerRecord.remoteStorage):
                raise Exception, 'Cannot lower quota below current storage.\n'
        if (None != localQuota):
            if (addQuotas):
                localQuota += peerRecord.localQuota
            elif (localQuota < peerRecord.localStorage):
                raise Exception, 'Cannot lower quota below current storage.\n'
        for item in ('email','remoteQuota','localQuota',
                     'comment','talk','listen','host','port'):
            if (eval(item)):
                print 'peerRecord.' + item + '=' + `eval(item)`
                exec('peerRecord.' + item + '=' + `eval(item)`)
        
        self.ResortPeers()

    def DeletePeer(self,peer):
        self.ComplainIfNoSuchPeer(peer)
        peerRecord = self.peerDatabase[peer]
        if (peerRecord.remoteStorage > 0 or
            peerRecord.localStorage > 0):
            raise NonZeroStoragePreventsDelete(peer,
                                               peerRecord.remoteStorage,
                                               peerRecord.localStorage)
        msg = ('DIBS account with ' + dibs_options.dibsPublicKey +
               ' has been deleted by peer.')
        try:
            MailDataToUser(msg,dibs_options.dibsAdmin,peerRecord.email,
                           dibs_options.smtpServer)
        except Exception, e:
            dibs_logger.Logger.PrintAndLog('Warning: error in mailing ' +
                                           'deleted user: ' + `e` ,
                                           dibs_logger.LOG_ERROR)
        os.rmdir(self.GetNameForPeerDir(peer))
        del self.peerDatabase[peer]
        self.ResortPeers()


    def GetAddressForPeer(self,peer):
        peerRecord = self.peerDatabase[peer]
        return peerRecord.email

    def GetCommunicationPrefsForPeer(self,peer):
        peerRecord = self.peerDatabase[peer]
        return (peerRecord.host, peerRecord.port, peerRecord.talk)

    def FindPeerToStorePiece(self,pieceSize):
        if (not self.peerDatabase):
            raise NoPeersToTradeWith

        for peerNum in range(len(self.sortedPeerList)):
            peer = self.sortedPeerList[peerNum][1]
            if (self.peerDatabase[peer].RemainingRemoteStorage() > pieceSize):
                if (peerNum > 0):
                    # Whoever was at the front of the list did not have
                    # enough space so sort the list.
                    self.ResortPeers()
                else: # Move the peer we choose to the end of the list
                    self.sortedPeerList.append(self.sortedPeerList.pop(0))
                return peer

        # If we get here then none of the peers have room for the piece.
        raise NoPeersToTradeWith

    def ResortPeers(self):
        """
        Create and sort the sortedPeerList.

        This function makes self.sortedPeerList into a list of pairs of
        the form (space, peer) where space reprsents how much space the
        corresponding peer has left for us.  Calling ResortPeers makes
        self.sortedPeerList be sorted in decreasing order of space.
        """
        
        self.sortedPeerList = []
        append = self.sortedPeerList.append
        for i in self.peerDatabase.keys():
            append((self.peerDatabase[i].RemainingRemoteStorage(), i))
        self.sortedPeerList.sort()
        self.sortedPeerList.reverse() 

    def UnstorePiecesForFile(self,file):
        """
        Tell the database to delete information about storing the given
        file.  Also, return a list of peers and pieces so that the
        caller can send messages to the peers to tell them they can
        stop storing the pieces.
        """
        result = self.GetPeersAndPiecesForFile(file)
        for pieceData in result:
            self.peerDatabase[pieceData[1]].ModifyRemoteStorage(-pieceData[2])
        del self.fileDatabase[file]
        return result
    
    def GetPeersAndPiecesForFile(self,file):
        """
        Make a list of all the pieces of file and return that list.
        Each item in the list is a tuple of the form (pieceName,peer,size).
        Note that pieces mrked as lost are ignored.
        """
        if (not self.fileDatabase.has_key(file)):
            raise LocalFileNonExistent, file
        fileRecord = self.fileDatabase[file]
        result = []
        append = result.append
        for pieceName in fileRecord.pieces.keys():
            pieceRecord = fileRecord.pieces[pieceName]
            if (pieceRecord.StoredP()):
                append((pieceName,pieceRecord.GetPeer(),pieceRecord.size))
                # Note: we set append=result.append before the for loop.
            else:
                dibs_logger.Logger.PrintAndLog('WARNING: ignoring ' +
                                               'piece "' + pieceName
                                               + '" because it was marked '
                                               + 'as lost.\n',
                                               dibs_logger.LOG_WARNING)
        return result

    def GetHashForFilePiece(self,file,pieceName):
        if (not self.fileDatabase.has_key(file)):
            raise LocalFileNonExistent, file
        fileRecord = self.fileDatabase[file]
        return fileRecord.pieces[pieceName].GetHash()
            
    def UnstorePieceForPeerOnOurMachine(self,peer,pieceName,pieceSize,
                                        cmdTime):
        """
        The argument cmdTime is the time the unstore request was issued
        (according to the clock on the issuers machine).  Therefore
        if cmdTime is greater than the storage time of pieceName stored
        for peer, then stop storing pieceName on our machine and update our
        database to give back the appropriate storage.

        Otherwise raise an exception to report that the unstore request
        was ignored due to stale command time.  
        """

        storeCmdTime = self.peerDatabase[peer].storedData[pieceName]
        if (storeCmdTime < cmdTime):
            self.peerDatabase[peer].ModifyLocalStorage(-pieceSize)
            del self.peerDatabase[peer].storedData[pieceName]
        else:
            raise UnstoreIgnoredBecauseStaleTime, (cmdTime, storeCmdTime)

    def RememberRecoverAllRequest(self):
        for peer in self.peerDatabase.keys():
            self.peersRespondingToRecoverAll[peer] = 0
        
    def RememberAttemptingToRecoverFile(self,fileName):
        
        if (self.recoveryDatabase.has_key(fileName)):
            dibs_logger.Logger.PrintAndLog(string.join(
                ['\n\nWARNING: Re-attempting to recover file ',
                 fileName,'.\n\n'],''),dibs_logger.LOG_WARNING)

        self.recoveryDatabase[fileName] = RecoveryAttempt(
            fileName,
            self.fileDatabase[fileName].GetMinPiecesNeededForRecovery())
                                                          
    def RememberPieceOfFileRecovered(self,file,pieceNum,pieceFile):
        """
        Remember that we recovered piece number pieceNum of file.
        If that was the last piece needed, return true and delete
        the recovery record.  Otherwise return false.
        Note that if we are doing a recover_all and the recovery
        record for the file is partially empty then we fill it in
        using the data in pieceFile
        
        """

        recoveryRec = self.recoveryDatabase[file]
        if (recoveryRec.PartiallyEmpty()):
            recoveryRec.CompletePartiallyEmptyRecordFromPiece(pieceFile)
        recoveryRec.RememberPieceRecovered(pieceNum)
        if (recoveryRec.RecoveredEnoughPieces()):
            return 1
        else:
            return 0

    def RememberAttemptingToProbeFile(self,fileName):

        if (self.probeDatabase.has_key(fileName)):
            dibs_logger.Logger.PrintAndLog(string.join(
                ['\n\nWARNING: Re-attempting to probe piece ',
                 fileName,'.\nOld probe data will be lost.\n\n'],''),
                                           dibs_logger.LOG_WARNING)


        self.probeDatabase[fileName] = ProbeAttempt(
            fileName,
            self.fileDatabase[fileName].GetMinPiecesNeededForRecovery(),
            self.GetPeersAndPiecesForFile(fileName))

    def RememberPieceOfFileProbed(self,file,pieceNum,pieceName,hash):
        """
        Remember that we succesfully probed piece number pieceNum of file.
        """

        storedHash = self.GetHashForFilePiece(file,pieceName)
        probeResult = (hash == storedHash) 
        dibs_logger.Logger.PrintAndLog('Stored hash for piece = ' +
                                       `storedHash` + ' and hash from probe = '
                                       + `hash` + '.\n',dibs_logger.LOG_DEBUG)
        if (self.probeDatabase.has_key(file)):
            probeRec = self.probeDatabase[file]
            probeRec.RememberPieceProbed(pieceNum,pieceName,probeResult)
            if (probeRec.ProbeCompletedP()):
                self.CloseProbeAttempt(file)
        else:
            dibs_logger.Logger.PrintAndLog(
                'Received unexpected probe response for file ' + `file` +
                '.\nPerhaps you deleted the probe database while the probe\n' +
                'was in progress.  Unexpected probe ignored.\n.',
                dibs_logger.LOG_WARNING)
        return probeResult
    
    def CloseProbeAttempt(self,fileName):
        self.probeDatabase[fileName].RecordProbeStats(self)
        del self.probeDatabase[fileName]

    def GetStaleProbes(self):
        return filter(lambda x: self.probeDatabase[x].TooOldP(),
                      self.probeDatabase.keys())

    def CloseOldProbes(self):
        for fileName in self.GetStaleProbes():
            self.CloseProbeAttempt(fileName)

    def GetRandomStoredFilename(self):
        return self.fileDatabase.keys()[
            random.randrange(0,len(self.fileDatabase))]

    def NumStoredFiles(self):
        return len(self.fileDatabase)

    def GetNamesOfRecoveryPieces(self,file):
        """
        Return a list of names of the piece files for file.

        Note: Just the file names are returned, the caller is
        responsible for getting the directory where they are
        stored.
        """
        assert self.recoveryDatabase.has_key(file), (
            'recoveryDatabase has no record for ' + file + '.\n'
            + 'Keys = ' + `self.recoveryDatabase.keys()` + '\n')
        return self.recoveryDatabase[file].GetNamesOfPieces()

    def StillNeedToRecover(self,file):
        """
        Since we use erasure correcting codes in storing files, we
        may finish recovering file before all peers have sent us
        the piece of file that they are storing.

        This function returns true if we still need to recover file
        and returns false if we have already recovered file and therefore
        do not need any more pieces.
        """
        if (self.DoingRecoverAllP()):
            if (self.recoveryDatabase.has_key(file)):
                return not self.recoveryDatabase[file].RecoveredEnoughPieces()
            else:
                self.recoveryDatabase[file] = RecoveryAttempt(file,None)
                return 1
        else:
            return self.recoveryDatabase.has_key(file)

    def CompleteRecoveryRequest(self,file):
        if (not self.DoingRecoverAllP()):
            del self.recoveryDatabase[file]
            dibs_logger.Logger.PrintAndLog('Finished recover file ' + file,
                                           dibs_logger.LOG_INFO)

    def PeerDoneRespondingToRecoverAllRequest(self,peer):
        self.peersRespondingToRecoverAll[peer] = 1
        if (len(self.peersRespondingToRecoverAll)
            == reduce(lambda x,y:x+y,
                      self.peersRespondingToRecoverAll.values())):
            # all peers responded
            self.peersRespondingToRecoverAll = {}
            self.RemoveCompletedRecoveryRecords()
            if (dibs_options.mailUserOnRecovery):
                self.MailUserThatRecoverAllFinished()

    def RemoveCompletedRecoveryRecords(self):
        for record in self.recoveryDatabase.keys():
            if (self.recoveryDatabase[record].RecoveredEnoughPieces()):
                del self.recoveryDatabase[record]

    def DoingRecoverAllP(self):
        return len(self.peersRespondingToRecoverAll)

    def ClearLocalDB(self):
        for peer in self.peerDatabase.keys():
            self.peerDatabase[peer].ZeroRemoteStorage()
        self.fileDatabase = {}

    def PeerKnownP(self,peer):
        return self.peerDatabase.has_key(peer)

    def ComplainIfNoSuchPeer(self,peer):
        if (not self.PeerKnownP(peer)):
            raise UnknownPeerException(peer)

    def ForgetPeersPieces(self,peer):
        """
        Remove any pieces of files we are storing for peer and update
        the peerDatabase to note this.
        """
        self.ComplainIfNoSuchPeer(peer)
        self.peerDatabase[peer].localStorage = 0
        for pieceName in self.peerDatabase[peer].storedData.keys():
            fileName = self.GetNameForPeerFile(pieceName,peer)
            try:
                os.remove(fileName)
            except Exception, e:
                msg = ('WARNING: Could not remove file "' + fileName +
                       '" because of exception "' + `e` + '", continuing.')
                dibs_logger.Logger.PrintAndLog(msg,dibs_logger.LOG_ERROR)
        self.peerDatabase[peer].storedData = {}

    def PeerForgotUs(self,peer):
        """
        A peer forgot us so reflect this in the database.  Specifically,
        make sure we set our remoteStorage with peer to 0 and change
        the status of all pieces that peer was storing for us to LOST.
        """

        filesAffected = []
        self.peerDatabase[peer].ZeroRemoteStorage()
        for fileName in self.fileDatabase.keys():
            fileRecord = self.fileDatabase[fileName]
            lost = fileRecord.MarkPiecesFromPeerAsLost(peer)
            if (lost):
                filesAffected.append(fileName)
        return filesAffected

    def RememberContractPosted(self,contract,url):
        if (self.postedContractDatabase.has_key(contract.name)):
            dibs_logger.PrintAndLog('Duplicate contract posted.',
                                    dibs_logger.LOG_WARNING)
        self.postedContractDatabase[contract.name] = contract
        if ('none' != url.lower()):
            r = contract.PostToContractServer(
                url,dibs_crypto.GetKey(dibs_options.dibsPublicKey))
            if ('OK' != string.strip(r)):
                raise PostContractFailed, (contract,url,r)

    def ForgetPeerContract(self,name,url):
        """
        Forget the previously posted contract with the given name
        and if 'none' != url.lower(), remove the contract from the
        given url.  Note that being able to provide 'none' for the
        url is useful if your database gets out of sync with the
        contract server and has contracts which the server has
        forgotten about.
        """
        if (self.postedContractDatabase.has_key(name)):
            if ('none' != url.lower()):
                r = self.postedContractDatabase[name].UnpostToContractServer(
                    url)
                if ('OK' != string.strip(r)):
                    raise UnpostContractFailed, (name,url,r)
            del self.postedContractDatabase[name]
        else:
            dibs_logger.Logger.PrintAndLog('No contract named ' + `name` +
                                           ' exists.',dibs_logger.LOG_WARNING)

    def RememberContractProposed(self,proposal):
        if (self.proposedContractDatabase.has_key(proposal.contractName)):
            dibs_logger.Logger.PrintAndLog('Duplicate contract proposed.',
                                    dibs_logger.LOG_WARNING)
        self.proposedContractDatabase[proposal.contractName] = proposal

    def RemoveProposalForContract(self,contractName):
        result = self.proposedContractDatabase[contractName]
        del self.proposedContractDatabase[contractName]
        return result

    def FileBackedUpP(self,file):
        return self.fileDatabase.has_key(file)

    def HashForStoredFile(self,file):
        return self.fileDatabase[file].hash

    def GetPiecesForPeer(self,peer):
        "Return a list of names of pieces we are storing for peer."

        self.ComplainIfNoSuchPeer(peer)
        return self.peerDatabase[peer].storedData.keys()

    def GetPeers(self):
        return self.peerDatabase.keys()

    def GetNameForPeerFile(self,pieceName,peer):
        self.ComplainIfNoSuchPeer(peer)
        hName = HashToFileName(pieceName)
        return (PathJoin(
            self.GetNameForPeerDir(peer),
            reduce(lambda x,y: PathJoin(x,y),
                   list(hName[0:dibs_constants.storageDirDepth])+[hName])))

    def GetNameForPeerDir(self,peer):
        return PathJoin(dibs_options.DIBS_DIR,peer)

    def GetAllPeerDirs(self):
        dirs = []
        for peer in self.peerDatabase.keys():
            dirs.append(PathJoin(dibs_options.DIBS_DIR,peer))
        return dirs

    def GetNameForRecoveryDir(self):
        return dibs_options.recoveryDir

    def GetContractByName(self,name):
        if (self.postedContractDatabase.has_key(name)):
            return self.postedContractDatabase[name]
        else:
            return None
