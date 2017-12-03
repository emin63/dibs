
import time, string, cPickle, os
from math import sqrt

class ProbeStatsRecord:

    def __init__(self):
        self.numFailedProbes = 0L
        self.numTimeouts = 0L
        self.numGoodProbes = 0L
        self.totalResponseTimes = 0.0
        self.totalSquaredResponseTimes = 0.0

    def __str__(self):
        if (self.numGoodProbes > 0):
            mean = self.totalResponseTimes/float(self.numGoodProbes)
            stddev = (self.totalSquaredResponseTimes/float(self.numGoodProbes)
                      - mean*mean)
            mean = round(mean)
            if (stddev > 0):
                stddev = round(sqrt(stddev))
            else:
                stddev = 'n/a'
        else:
            mean = 'n/a'
            stddev = 'n/a'

        totalProbes = self.numGoodProbes+self.numTimeouts+self.numFailedProbes
        
        return ('{\n\tFAILED_PROBES = ' + `self.numFailedProbes`  + '\n\t' +
                'TIMEOUTS = ' + `self.numTimeouts` + '\n\t' +
                'GOOD_PROBES = ' + `self.numGoodProbes` + '\n\t' +
                'MEAN_RESPONSE_TIME = ' + `mean` + ' +/- ' +
                `stddev` + '\n\t' + '}')

    def RecordProbeGood(self,responseTime):
        self.numGoodProbes += 1
        self.totalResponseTimes += responseTime
        self.totalSquaredResponseTimes += responseTime*responseTime

    def RecordTimeout(self):
        self.numTimeouts += 1

    def RecordProbeFailed(self):
        self.numFailedProbes += 1

    def Copy(self,other):
        self.numFailedProbes = other.numFailedProbes 
        self.numTimeouts = other.numTimeouts 
        self.numGoodProbes = other.numGoodProbes 
        self.totalResponseTimes = other.totalResponseTimes 
        self.totalSquaredResponseTimes = other.totalSquaredResponseTimes 

    def Merge(self,other):
        self.numFailedProbes += other.numFailedProbes 
        self.numTimeouts += other.numTimeouts 
        self.numGoodProbes += other.numGoodProbes 
        self.totalResponseTimes += other.totalResponseTimes 
        self.totalSquaredResponseTimes += other.totalSquaredResponseTimes 

class PeerErrorStatsRecord:

    def __init__(self):
        self.errors = {}

    def __str__(self):
        return `self.errors`

    def RecordError(self,type,date):
        if (not self.errors.has_key(type)):
            self.errors[type] = []
        self.errors[type].append(date)

class ConnectionStatsRecord:

    def __init__(self):
        self.numConnections = 0L
        self.errors = {}
        self.totalXfer = 0.0
        self.totalSquaredXfer = 0.0

    def __str__(self):
        mean = self.totalXfer/self.numConnections
        return ('{ CONNECTIONS = ' + `self.numConnections`  + '\n\t' +
                'ERRORS = ' + `self.errors` + '\n\t' +
                'AVERAGE_TRANSFER = ' +
                `round(mean)` + ' +/- ' +
                `round(sqrt(self.totalSquaredXfer/self.numConnections -
                            mean*mean))`
                + '}')
        

    def Copy(self):
        result = ConnectionStatsRecord()
        result.numConnections = self.numConnections
        result.errors = dict(self.errors)
        result.totalXfer = self.totalXfer
        result.totalSquaredXfer = self.totalSquaredXfer
        return result

    def Merge(self,other):
        self.numConnections += other.numConnections
        self.totalXfer += other.totalXfer
        self.totalSquaredXfer += other.totalSquaredXfer
        for errorType in other.errors.keys():
            if (not self.errors.has_key(errorType)):
                self.errors[errorType] = 0
            self.errors[errorType] += other.errors[errorType]

    def RecordConnection(self,error,xfer):
        self.numConnections += 1
        if (error):
            if (not self.errors.has_key(error)):
                self.errors[error] = 0
            self.errors[error] += 1
        else:
            self.totalXfer += xfer
            self.totalSquaredXfer += xfer*xfer

class DIBSStatDatabase:
    """
    This class implements a record to keep track of DIBS statistics.
    """

    def __init__(self):
        self.startDate = time.time()
        self.errorsWithPeer = {}
        self.connectionsTo = {}
        self.connectionsFrom = {}
        self.probesOfPeer = {}

    def Show(self):
        msg = ['{\tSTART_DATE = ' +
               time.asctime(time.localtime((self.startDate))) + '\n' +
               '\tERRORS_WITH_PEER = {' ]
        for peer in self.errorsWithPeer:
            msg.append('\t\t ' + `peer` + ' = { ' +
                       self.errorsWithPeer[peer].__str__() + ' }')
        msg.append('\t}\n\tCONNECTIONS_TO = {')
        for con in self.connectionsTo:
            msg.append('\t\t ' + `con` + ' = { ' +
                       self.connectionsTo[con].__str__() + ' }')
        msg.append('\t}\n\tCONNECTIONS_FROM = {')
        for con in self.connectionsFrom:
            msg.append('\t\t ' + `con` + ' = { ' +
                       self.connectionsFrom[con].__str__() + ' }')
        msg.append('\t}\n\tPROBES_OF_PEERS = {')
        for peer in self.probesOfPeer:
            msg.append('\t\t ' + `peer` + ' = { ' +
                       self.probesOfPeer[peer].__str__() + ' }')
        msg.append('\t}\n}\n')
        return string.join(msg,'\n')
             

    def DumpToFile(self,fileName):
        fd = open(fileName,'wb')
        cPickle.dump(self,fd)
        fd.close()

    def ImportFromFile(self,fileName):
        if (os.path.exists(fileName)):
            fd = open(fileName,'rb')
            other = cPickle.load(fd)
            fd.close()
            self.Import(other)
            return 1
        else:
            return 0


    def Import(self,other):
        """
        Given another DIBSStatDatabase add all the records from other.
        """
        self.startDate = min(self.startDate,other.startDate)

        for peer in other.errorsWithPeer.keys():
            record = other.errorsWithPeer[peer]
            for error in record.errors:
                self.AddErrorWithPeer(peer,error[0],error[1])

        for peer in other.connectionsTo.keys():
            record = other.connectionsTo[peer]            
            if (not self.connectionsTo.has_key(peer)):
                self.connectionsTo[peer] = record.Copy()
            else:
                self.connectionsTo[peer].Merge(record)

        for peer in other.connectionsFrom.keys():
            record = other.connectionsFrom[peer]            
            if (not self.connectionsFrom.has_key(peer)):
                self.connectionsFrom[peer] = record.Copy()
            else:
                self.connectionsFrom[peer].Merge(record)

        for peer in other.probesOfPeer.keys():
            record = other.probesOfPeer[peer]            
            if (not self.probesOfPeer.has_key(peer)):
                self.probesOfPeer[peer] = record.Copy()
            else:
                self.probesOfPeer[peer].Merge(record)

    def AddErrorWithPeer(self,peer,type,date):
        if (not self.errorsWithPeer.has_key(peer)):
            self.errorsWithPeer[peer] = PeerErrorStatsRecord()
        self.errorsWithPeer[peer].RecordError(type,date)

    def NoteConnectionTo(self,peer,error,xfer):
        if (not self.connectionsTo.has_key(peer)):
            self.connectionsTo[peer] = ConnectionStatsRecord()
        self.connectionsTo[peer].RecordConnection(error,xfer)

    def NoteConnectionFrom(self,peer,error,xfer):
        if (not self.connectionsFrom.has_key(peer)):
            self.connectionsFrom[peer] = ConnectionStatsRecord()
        self.connectionsFrom[peer].RecordConnection(error,xfer)

    
    def RecordProbeGood(self,peer,responseTime):
        if (not self.probesOfPeer.has_key(peer)):
            self.probesOfPeer[peer] = ProbeStatsRecord()
        self.probesOfPeer[peer].RecordProbeGood(responseTime)

    def RecordProbeTimeout(self,peer):
        if (not self.probesOfPeer.has_key(peer)):
            self.probesOfPeer[peer] = ProbeStatsRecord()
        self.probesOfPeer[peer].RecordTimeout()

    def RecordProbeFailed(self,peer):
        if (not self.probesOfPeer.has_key(peer)):
            self.probesOfPeer[peer] = ProbeStatsRecord()
        self.probesOfPeer[peer].RecordProbeFailed()
