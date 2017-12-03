
import dibs_options
from templates import *
from dibs_utils import *

class AutoCheckCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

    def run(self,argv=None,parentWindow=None):
        self.PrepareForDIBSCommand()
        
        if (None != argv):
            self.ParseRequiredArgs(argv)

        import dibs_main
        d = dibs_main.DIBS(self.database)
        dir = dibs_options.autoBackupDir
        for file in os.listdir(dir):
            d.StoreAsNecessary(os.path.abspath(PathJoin(dir,file)),PathJoin(
                dibs_options.rootDir+'autoBackup',file))
            d.SendOutgoingMessages()

        self.FinishDIBSCommand()

class StoreCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.RequiredArg('name=',ExistingFileNameValidator(),"""
        Name of a file or directory to store.
        """)
        self.OptionalArg('as=',StringValidator(),"""
        Optional alternative name to store under.
        """)
        
    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        self['name'] = os.path.abspath(self['name'])
        if (None == self['as'] or '' == self['as']):
            self['as'] = self['name']

        import dibs_main
        d = dibs_main.DIBS(self.database)
        d.StoreAsNecessary(self['name'],self['as'])
        d.SendOutgoingMessages()

        self.FinishDIBSCommand()

class UnstoreFileCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.RequiredArg('file=',StringValidator(),"""
        Name of file to unstore.
        """)

    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        d.UnstoreFile(self['file'])

        self.FinishDIBSCommand()


class RecoverFileCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)
        self.RequiredArg('file=',StringValidator(),"""
        Name of file to recover.
        """)

    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        d.RecoverFile(self['file'])

        self.FinishDIBSCommand()        

class RecoverAllCmd(DIBSCommand):

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        d.RecoverAll()

        self.FinishDIBSCommand()
