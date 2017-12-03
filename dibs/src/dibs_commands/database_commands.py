
import dibs_options
from templates import *
from dibs_utils import *

class ShowDatabaseCmd(DIBSCommand):
    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.onlyOptionsMapping = {
            'peer_info': (lambda d : d.database.ShowPeerInfo),
            'peers': (lambda d : d.database.ShowPeerDatabase),
            'files': (lambda d : d.database.ShowFileDatabase),
            'file_list': (lambda d : d.database.ShowFileDatabaseKeys),
            'recovery': (lambda d : d.database.ShowRecoveryDatabase),
            'probe': (lambda d : d.database.ShowProbeDatabase),
            'stats': (lambda d : d.database.statsDatabase.Show),
            'storage': (lambda d : d.database.ShowStorage), 
            'posted_contracts': (
            lambda d :d.database.ShowPostedContractDatabase),
            'proposed_contracts': (
            lambda d : d.database.ShowProposedContractDatabase)
            }


        self.OptionalArg('only=',ChooseOneFromListValidator(
            self.onlyOptionsMapping.keys()+ [''],''),"""
            Show all entries in the database.  If the only option is used,
            then only options in the specified part of the database are
            shown.
            """)

    def run(self,argv=None,parentWindow=None):
        self.PrepareForDIBSCommand()

        if (None != argv):
            self.ParseRequiredArgs(argv)                

        import dibs_main
        d = dibs_main.DIBS(self.database)

        if (None == self['only'] or '' == self['only'].strip()):
            result = d.database.__str__()
        elif (self.onlyOptionsMapping.has_key(self['only'])):
            result = self.onlyOptionsMapping[self['only']](d)()
        else:
            msg = ('Unknown option for --only : "' + self['only'] + '".'
                   + '\nPossible values are ' + `onlyOptionsMapping.keys()`)
            raise Exception, msg

        self.FinishDIBSCommand()

        return result

class CleanupCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

    def run(self,argv=None,parentWindow=None):
        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        d.Cleanup()

        self.FinishDIBSCommand()

class ClearDBCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)
                             
    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        d.ClearDB()

        self.FinishDIBSCommand()


class MergeStatsDBCmd(DIBSCommand):
    """
    Merge in a existing statistics database with the current one.
    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)


    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        global gFileToMoveOnError        
        for file in os.listdir(dibs_options.statsMsgDir):
            fullFileName = PathJoin(dibs_options.statsMsgDir,file)
            gFileToMoveOnError = fullFileName                
            d.database.statsDatabase.ImportFromFile(fullFileName)
            os.remove(fullFileName)

        self.FinishDIBSCommand()


class ProbeFileCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)
        self.OptionalArg('file=',StringValidator(),"""
        Name of file to probe.
        """)

    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)

        if (None == self['file']):
            self['file'] = ''
        if (not self['file'] and d.database.NumStoredFiles() > 0):
            d.PrintAndLog('Cleaning out stale probes.')
            d.database.CloseOldProbes()
            fileName = d.database.GetRandomStoredFilename()
            d.PrintAndLog('Probing random file ' + `fileName`)
            d.ProbeFile(fileName)
        else:
            d.ProbeFile(self['file'])
            d.PrintAndLog('Sending probe requests for file '
                          + self['file'] + '.')

        self.FinishDIBSCommand()
