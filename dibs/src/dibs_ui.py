#!/usr/bin/python

import string
import re
import sys
import os, os.path
import time
import tempfile
from getopt import getopt

from dibs_commands.templates import RemoveLock
from dibs_utils import *

global gFileToMoveOnError
gFileToMoveOnError = ''

def InitializeDIBSCmd():
    """
    Create the necessary files and directories for DIBS.
    """

    import dibs_database

    if (not os.path.exists(PathJoin(dibs_options.DIBS_DIR,'dibsrc.py'))):
        fd = open(PathJoin(dibs_options.DIBS_DIR,'dibsrc.py'),'w')
        fd.write('# you can put customization commands here.\n')
        fd.close()
        d = dibs_database.DIBSDatabase()
        d.SaveToFile(dibs_options.databaseFilePrefix)
        print 'Successfully initialized DIBS.\n'

def CreateDIBSDirIfNecessary():
    for dir in [dibs_options.DIBS_DIR,dibs_options.recoveryDir,
                dibs_options.autoBackupDir,
                dibs_options.outgoingQueueDir,
                dibs_options.incomingQueueDir,
                dibs_options.statsMsgDir]:
        if (not os.path.exists(dir)):
            print '\n\nCreating directory ' + dir + '.\n\n'
            os.mkdir(dir)
    InitializeDIBSCmd()


def GetSendersInFile(file):
    result = ''
    if (os.path.exists(file)):
        fd = open(file,'rU')
        m = re.search('(?m)^(From|Sender|X-Envelope-From):(.+)$',fd.read())
        fd.close()
        if (m):
            possibleAddrs = string.split(m.group(2),)
            for item in possibleAddrs:
                m = re.search('( *|^ *)<?([^ @<>]+@[^ <>]+)>?',item)
                if (m):
                    result = result + m.group(2)
                
    return result

def MaybeMailErrorMsgToInterestedParties(msg):

    recipients = ''
    mailCmds = ['process_message','start_daemon','auto_check','poll_passives',
                'send_message','merge_stats']
   
    for cmd in mailCmds:
        if (sys.argv.count(cmd)):
            exceptionTypeRE = re.compile("Exception of type '<class dibs_lib.dibs_exceptions.([^ ]+) ")
            m = exceptionTypeRE.search(msg)
            
            for i in range(0,len(sys.argv)):
                if (sys.argv[i] == 'file' and i <= len(sys.argv)):
                    recipients = string.join(GetSendersInFile(sys.argv[i+1]),
                                             '')
            if (string.strip(dibs_options.dibsAdmin)):
                recipients = recipients + ' ' + dibs_options.dibsAdmin
            else:
                recipients = string.join([recipients,os.environ['USER'],'@',
                                          os.environ['HOST']],'')

        if (string.strip(recipients)):
            recipients = string.join(string.split(recipients),',')
            print 'mailing error msg to ' + recipients
            msg = MailErrorMsgToUser(
                msg,dibs_options.dibsAdmin,recipients,
                dibs_options.errWarnCount,dibs_options.errMaxCount,
                dibs_options.errorDir,dibs_options.smtpServer)
            print msg
            return

def StartDIBSGUI():
    print 'Starting GUI.'
    import dibs_gui
    root = dibs_gui.StartGUI()
    print 'Exiting GUI normally.'

######################################################################
#
# Start processing here

try:

    import dibs_options
    from dibs_utils import *

    CreateDIBSDirIfNecessary()

    from dibs_commands.communication_commands import StopDaemonCmd, StartDaemonCmd, PollPassivesCmd, SendHelloCmd, ProcessMessageCmd, SendMessageCmd
    from dibs_commands.database_commands import ShowDatabaseCmd, CleanupCmd, ClearDBCmd, MergeStatsDBCmd, ProbeFileCmd
    from dibs_commands.contract_commands import PostPeerContractCmd, ProposePeerContractCmd, UnpostPeerContractCmd
    from dibs_commands.storage_commands import AutoCheckCmd, StoreCmd, UnstoreFileCmd, RecoverFileCmd, RecoverAllCmd
    from dibs_commands.peer_commands import AddPeerCmd, EditPeerCmd, DeletePeerCmd, ForgetPeerCmd

    cmds = {'add_peer' : AddPeerCmd,
            'edit_peer' : EditPeerCmd,
            'delete_peer' : DeletePeerCmd,
            'store' : StoreCmd, 
            'unstore_file' : UnstoreFileCmd,
            'probe' : ProbeFileCmd,
            'recover_file' : RecoverFileCmd,
            'recover_all' : RecoverAllCmd,
            'merge_stats' : MergeStatsDBCmd,
            'send_hello'  : SendHelloCmd,
            'stop_daemon'  : StopDaemonCmd,
            'show_database' : ShowDatabaseCmd,
            'cleanup' : CleanupCmd,
            'process_message' : ProcessMessageCmd,
            'auto_check' : AutoCheckCmd,
            'clear' : ClearDBCmd,
            'forget' : ForgetPeerCmd,
            'poll_passives' : PollPassivesCmd,
            'send_message' : SendMessageCmd,
            'post_contract' : PostPeerContractCmd,
            'unpost_contract' : UnpostPeerContractCmd,
            'propose_contract' : ProposePeerContractCmd
            }

    if (len(sys.argv) <= 1):
        StartDIBSGUI()
    elif (cmds.has_key(sys.argv[1])):
        import dibs_logger
        dibs_logger.Logger.PrintAndLog('Calling command ' + sys.argv[1],
                                       dibs_logger.LOG_DEBUG)
        c = cmds[sys.argv[1]](sys.argv[1])
        result = c.run(sys.argv)
        if (None != result):
            print result
    elif('start_daemon' == sys.argv[1]):

        # Set logFile to daemonLogFile so that we don't clobber logging
        # from a concurrently running dibs program.
        import dibs_logger

        del dibs_logger.Logger
        dibs_logger.Logger = dibs_logger.DIBSLogger(
            dibs_options.daemonLogFile,dibs_options.logLevel,
            dibs_options.printLogLevel)
        import dibs_daemon

        daemon = dibs_daemon.DIBSServer(dibs_options.daemonPort)
        sys.exit(0)
    else:
        msg = string.join(['Unknown command \'',sys.argv[1],'\'.\n',
                           'Possible commands are ',
                           string.join(cmds.keys(),' '),'.\n\n'],'')
        print msg
        sys.exit(1)
except SystemExit, e:
    RemoveLock()
    sys.exit(e)
except Exception, e:
    RemoveLock()
    if (-1 != e.__str__().find('NoBigDealException')):
        e.Report()
        sys.exit(0)

    msg = ('Subject: <DIBS> DIBS ERROR\n' + '\n' + 
          'Command was \'' + `sys.argv` + '\'.\n\n' + 
          'Exception of type \'' + `sys.exc_type` + '\':  \'' + 
           e.__str__() + '\'.\n\n\n' +
           GetTracebackString(sys.exc_info()))
    print msg    
    if (gFileToMoveOnError):
        tmpName = tempfile.mktemp()
        MoveFile(gFileToMoveOnError,tmpName)
        msg = msg + '\n\n\nOffending file moved to ' + tmpName + '.\n'
    print msg

    MaybeMailErrorMsgToInterestedParties(msg)
    
    print 'Not saving database.'

    sys.exit(1)
    
    

    
