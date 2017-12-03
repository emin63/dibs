
"""
This module implements a Graphical User Interface (GUI) for DIBS.
The main function is StartGUI, which creates a Tk window and enters
the Tk main loop until the user kills/quits the GUI.

When new commands are added, the AddDIBSCommandMenu function should
be modified accordingly.

"""

import sys, traceback, string
import Tkinter
import tkMessageBox
from Tkinter import Tk

from dibs_commands import templates
from dibs_commands.communication_commands import StopDaemonCmd, StartDaemonCmd, PollPassivesCmd, SendHelloCmd, ProcessMessageCmd, SendMessageCmd
from dibs_commands.database_commands import ShowDatabaseCmd, CleanupCmd, ClearDBCmd, MergeStatsDBCmd, ProbeFileCmd
from dibs_commands.contract_commands import PostPeerContractCmd, ProposePeerContractCmd, UnpostPeerContractCmd
from dibs_commands.storage_commands import AutoCheckCmd, StoreCmd, UnstoreFileCmd, RecoverFileCmd, RecoverAllCmd
from dibs_commands.peer_commands import AddPeerCmd, EditPeerCmd, DeletePeerCmd, ForgetPeerCmd

def MakeMainDIBSWindow(root):
    """
    MakeMainDIBSWindow(root):

    root:  An existing empty toplevel window.

    This function adds the title, menus, buttons, etc., to create the
    main window for the DIBS GUI.
    
    """
    
    root.title('Distributed Internet Backup System (DIBS)')
    
    menubarFrame = Tkinter.Frame(root,relief='raised',bd=2)
    commandDict = {}
    AddDIBSCommandMenu(menubarFrame,commandDict)
    #AddDIBSBrowseMenu(menubarFrame,commandDict)

    mainFrame = MakeDIBSMainFrame(root)
    
    menubarFrame.pack(side='top',expand=1,fill='x')
    mainFrame.pack(fill='both',expand=1,side='top')

    return root

def MakeDIBSMainFrame(root):
    """
    MakeDIBSMainFrame(root):

    root:  An existing empty toplevel window.

    Create the main frame for the DIBS main window and return the
    new frame.  The caller should pack/grid the frame as desired.
    """
    
    mainFrame = Tkinter.Frame(root)

    quitButton = Tkinter.Button(mainFrame,text='Quit',
                                command=lambda : root.destroy())
    quitButton.pack(fill='x',expand=1,side='left')

    helpButton = Tkinter.Button(mainFrame,
                                text='Help',
                                command=lambda : MakeMainHelpDialog())
    helpButton.pack(fill='x',expand=1,side='left')

    return mainFrame


def CreateSubMenuForCommandList(parentMenu,title,listOfNameCommandPairs,
                                commandDict):
    """
    CreateSubMenuForCommandList(parentMenu,title,listOfNameCommandPairs
                                commandDict):

    parentMenu:              Menu to create the new submenu in.
    title:                   Title of the submenu
    listOfNameCommandPairs:  A list of pairs of the form (name,cmd) where
                             name is a string and cmd is an instance of the
                             DIBSCommand class or a subclass of that class.
    commandDict:             A dictionary object that gets modified so that
                             commandDict[<<name>>] returns the
                             GenericGUICommand object associated with name.

    This function creates a new submenu, adds the given list of commands to the
    submenu, and returns the newly created menu.
    
    """
    submenu = Tkinter.Menu(parentMenu,tearoff=1)
    for pair in (listOfNameCommandPairs):
        commandDict[pair[0]] = GenericGUICommand(pair[1](pair[0]))
        submenu.add_command(label=pair[0],command=commandDict[pair[0]])
    parentMenu.add_cascade(label=title,menu=submenu)
    return submenu

def AddDIBSBrowseMenu(menubarFrame,commandDict):

    frame = Tkinter.Frame(menubarFrame)
    menuButton = Tkinter.Menubutton(frame)
    browseMenu = Tkinter.Menu(menuButton, tearoff=1)
    menuButton.configure(menu=browseMenu)
    menuButton.configure(text='Browse')
    frame.pack(side='left',expand=1,fill='x')
    menuButton.pack(side='left',expand=1,fill='x')

    browseMenu.add_command(label='My Contracts',command=
                           lambda : BrowseMyContracts(commandDict))

def BrowseMyContracts(commandDict):
    pass

def AddDIBSCommandMenu(menubarFrame,commandDict):
    """
    AddDIBSCommandMenu(menubarFrame,commandDict):

    menubarFrame:  A frame to create the menubar in.
    commandDict:             A dictionary object that gets modified so that
                             commandDict[<<name>>] returns the
                             GenericGUICommand object associated with name.

    This function creates the command menu and packs it into menubarFrame.
    """

    frame = Tkinter.Frame(menubarFrame)
    menuButton = Tkinter.Menubutton(frame)
    commandsMenu = Tkinter.Menu(menuButton, tearoff=1)
    menuButton.configure(menu=commandsMenu)
    menuButton.configure(text='Commands')
    frame.pack(side='left',expand=1,fill='x')
    menuButton.pack(side='left',expand=1,fill='x')

    contractMenu = CreateSubMenuForCommandList(commandsMenu,'Contracts',(
        ('post_contract',PostPeerContractCmd),
        ('propose_contract',ProposePeerContractCmd),
        ('unpost_contract',UnpostPeerContractCmd)),commandDict)

    backupMenu = CreateSubMenuForCommandList(commandsMenu,'Storage',(
        ('auto_check',AutoCheckCmd),('store',StoreCmd),
        ('unstore_file',UnstoreFileCmd),('recover_file',RecoverFileCmd),
        ('recover_all',RecoverAllCmd)),commandDict)

    communicationMenu = CreateSubMenuForCommandList(
        commandsMenu,'Communication',(
        ('start_daemon',StartDaemonCmd),('stop_daemon',StopDaemonCmd),
        ('send_hello',SendHelloCmd),('poll_passives',PollPassivesCmd),
        ('process_message',ProcessMessageCmd),('send_message',SendMessageCmd)),
        commandDict)

    databaseMenu = CreateSubMenuForCommandList(commandsMenu,'Database',(
        ('show_database',ShowDatabaseCmd),('clear',ClearDBCmd),
        ('forget_peer',ForgetPeerCmd),('cleanup',CleanupCmd),
        ('merge_stats',MergeStatsDBCmd),('probe',ProbeFileCmd)),commandDict)

    peerMenu = CreateSubMenuForCommandList(commandsMenu,'Peers',(
        ('forget_peer',ForgetPeerCmd),('add_peer',AddPeerCmd),
        ('edit_peer',EditPeerCmd),('delete_peer',DeletePeerCmd)),commandDict)
    

def MakeTextDialog(title,text,grab=0):
    """
    MakeTextDialog(title,text,grab=0):

    title:  Title of the dialog to create.
    text:   The text that the dialog should contain.
    grab:   Whether or not to execute a 'grab' and force the user
            to click OK before interacting with the rest of the
            application.

    This function creates a new dialog box with the given title and
    displays the given text in a (disabled) text widget.
    """
    window = Tkinter.Toplevel()
    window.title(title)
    yscroll=Tkinter.Scrollbar(window,orient='vertical')
    message = Tkinter.Text(window,yscrollcommand=yscroll.set)
    yscroll.config(command=message.yview)
    yscroll.pack(side='right',fill='y',expand=0)
    message.insert(Tkinter.END,str(text))
    message.config(state=Tkinter.DISABLED)
    message.pack(side='top',fill='both',expand=1)
    button = Tkinter.Button(window,text='OK',command = lambda:(
        window.tk.call('grab','release',window),window.destroy()))
    button.pack(side='top',fill='both',expand=1)
    if (grab):
        window.tk.call('grab','set',window)
    window.lift()

def MakeMainHelpDialog():
    """
    Make a dialog containing the main help for DIBS.
    """

    MakeTextDialog(title="DIBS Help",text="""
    
    The Distributed Internet Backup System (DIBS) is a program
    for automatically backing up your data over the Internet with
    other peers.  DIBS includes encryption, error correction coding,
    and many other neat features.  For downloads and detailed
    documentation, go to http://dibs.sourceforge.net.

    To use the DIBS gui, click on the Commands button, select the
    appropriate sub-menu for the type of command you would like,
    then select the command from the sub-menu.  This will open
    a dialog box for the given command.  Each command has its own
    help button describing how it works, as well as '?' buttons for
    describing the data expected by each argument.

    To get started, you will first need to add peers to trade
    backup space with.  If you already have a peer (or if you
    want to peer with another computer you control), you can manually
    enter peering information for the Peers-->add_peer command.
    A better method is to use the Contracts-->propose_contract
    command to automatically peer with someone who has posted a 
    contract to the contract server or to post your own advertisement
    for peering using the Contracts-->post_contract command.

    Once you have some peers in your database, you can either manually
    choose files/directories to backup using commands in the Storage
    menu (not recommended for beginners), are you can place links to
    the files/directories you want backed up in your .dibs/autoBackup
    directory and let DIBS daemon do things for you automatically.

    Finally, note that for DIBS to work properly, you need to either
    start the the Communication-->start_daemon command (recommended)
    or issue commands manually from the Communication menu (not
    recommended for beginners).
    """)
    
######################################################################
#
# Start functions to make a genric GUI command dialog
#

class GenericGUICommand:
    """
    The GenericGUICommand class is a class used to create a GUI command.
    It is used mainly by the CreateSubMenuForCommandList function to
    wrap a command into an object which a menubutton can point to.
    """
    
    def __init__(self,command):
        """
        __init__(self,command):

        command:   This should be a DIBSCommand object represent some command.
        """
        self.command = command
        self.command.entries = {}
        self.mainWindow = None

    def __call__(self):
        """
        __call__(self):

        Create a window to collect inputs for this command.
        """
        if (None != self.mainWindow):
            self.mainWindow.destroy()
            self.mainWindow = None
            self.entries = {}
        self.MakeMainCommandDialog()

    def MakeLabelAndEntryForSingleArgument(self,item,argFrame,row,doc):
        """
        MakeLabelAndEntryForSingleArgument(self,item,argFrame,row,doc):

        item:      Name of an argument.
        argFrame:  Frame to create the label and entry in.
        row:       Integer indicating which row to grid into.
        doc:       A string provided help docs for the argument.

        This function creates and grids a new lable and entry for the
        argument named by item.  Actually, the validator in
        self.command.arguments[item]['validator'] is used to create
        the menu entry.

        To modify or get the value for this argument, you can use
        self.entries[item].get() or self.entries[item].set(...).
        
        """
        label = Tkinter.Label(argFrame,text=item)
        validator = self.command.arguments[item]['validator']
        (menuEntry,entry) = validator.MakeMenuEntry(argFrame)
        helpButton = Tkinter.Button(argFrame,text='?',command=lambda:
                                    self.MakeHelpDialog(item,doc,
                                                        parent=argFrame))
        if (None == doc):
            helpButton.configure(state='disabled')
        self.command.entries[item] = entry
        label.grid(row=row,column=0,sticky='w')
        menuEntry.grid(row=row,column=1,sticky='w')
        helpButton.grid(row=row,column=2,sticky='w')

    def MakeLabelsAndEntrysForAllArguments(self,argFrame):
        """
        MakeLabelsAndEntrysForAllArguments(self,argFrame):

        argFrame:  Frame to put the arguments into.

        Creates labels and entries for all the required and optional
        arguments for self.command.
        """
        row=0

        if (len(self.command.orderedRequiredArgs) > 0):
            label = Tkinter.Label(argFrame,text='Required Arguments',
                                  relief='raised',padx=3,pady=3)

            label.grid(row=row,column=0,columnspan=3,sticky='wens')

            for item in self.command.orderedRequiredArgs:
                row += 1
                doc = self.command.arguments[item]['doc']
                self.MakeLabelAndEntryForSingleArgument(item,argFrame,row,doc)
            row+=1

        if (len(self.command.orderedOptionalArgs) > 0):
            label = Tkinter.Label(argFrame,text='Optional Arguments',
                                  relief='raised',padx=3,pady=3)
            label.grid(row=row,column=0,columnspan=3,sticky='wens')

            for item in self.command.orderedOptionalArgs:
                row += 1
                doc = self.command.arguments[item]['doc']
                self.MakeLabelAndEntryForSingleArgument(item,argFrame,row,doc)

    def MakeBottomButtonsForGUICommand(self,frame,window):
        """
        MakeBottomButtonsForGUICommand(self,frame,window):

        frame:  The frame to put the buttons into.
        window: The window to kill to cancel the command.

        Makes buttons that go on the bottom of a GUI command window.
              
        """
        okButton = Tkinter.Button(frame,text='OK',command=
                                  lambda : self.ProcessCommand(window))
        cancelButton = Tkinter.Button(frame,text='Cancel',command=
                                      lambda : self.CancelCommand(window))
        helpButton = Tkinter.Button(frame,text='Help',command=
                                    lambda : self.HelpCommand(window))
        okButton.pack(side='left',fill='both',expand=1)
        cancelButton.pack(side='left',fill='both',expand=1)
        helpButton.pack(side='left',fill='both',expand=1)

    def CancelCommand(self,window):
        window.destroy()
        self.mainWindow = None

    def HelpCommand(self,window):
        """
        HelpCommand(self,window):

        window:  Window representing the arguments and options for the command.

        This function shows the doc string for this command in a dialog
        box.
        """

        if ( None == self.command.__doc__ or 
             ('' == self.command.__doc__.strip()) ):
            self.command.__doc__ = """
            No documentation provided for this command.  Please see
            the manual that came with your DIBS installation or the
            online documentation available from http://dibs.sourceforge.net.
            """ 

        MakeTextDialog(title='Help for '+self.command.cmdName+' command',
                       text = self.command.__doc__)
        
        

    def ProcessCommand(self,window):
        """
        ProcessCommand(self,window):

        window:  Window representing the arguments and options for the command.

        This function processes the arguments the user enters, runs the
        command, and complains if something goes wrong.  The window is
        closed if the command is succesful but left open if something
        goes wrong so the user can fix the problem and try again.
        
        """
        try:        
            for arg in self.command.orderedRequiredArgs:
                argValue = self.command.entries[arg].get()
                argValue=self.command.arguments[arg]['validator'](argValue)
                self.command[arg] = argValue
                if (EmtpyP(arg)):
                    raise Exception, 'Missing value'
                    
            for arg in self.command.orderedOptionalArgs:
                argValue = self.command.entries[arg].get()
                if (argValue):
                    argValue=self.command.arguments[arg]['validator'](
                        argValue)
                    self.command[arg] = argValue
                else:
                    self.command[arg] = ''
            arg = None
            result = self.command.run()
            if (None != result):
                MakeTextDialog(title='Command Output',text=result,grab=1)
            window.destroy()
        except Exception, e:
            errTrace = ('Exception of type \'' + `sys.exc_type` + '\':  \'' + 
                         e.__str__() + '\'.\n\n\n' +
                         string.join(traceback.format_tb(sys.exc_info()[2])))
            self.ComplainAboutException(errTrace,arg,window,e)

    def ComplainAboutException(self,errTrace,arg,window,e):
        """
        ComplainAboutException(self,errTrace,arg,window,e):

        errTrace:  A traceback string describing the error in detail.
        arg:       Either None or the name of the argument being
                   processed when the error occured.
        window:    The window representing the command.
        e:         The exception object causing the problem.

        This funciton creates a dialog window describing the error and
        offering to show the user the error traceback if desired.
        """
        errMsg = e.__str__()
        self.command.RemoveMyLock()
        if (None != arg):
            errMsg += ('.\n\nError occured while processing argument '
                       + self.command.StripEq(arg) + '.')
        showTraceBack = window.tk.call('tk_dialog','.showTBOnErrorDialog',
                                       'DIBS Error',errMsg,'error',0,'OK',
                                       'Show Traceback')
        if (1 == showTraceBack or '1' == showTraceBack):
            tkMessageBox.showinfo('DIBS Traceback',errTrace,parent=window)

            
    def MakeHelpDialog(self,item,help,parent=None):
        MakeTextDialog('DIBS Help','Help on ' + item + ':\n\n' + help)
                            
    def MakeMainCommandDialog(self):
        """
        MakeMainCommandDialog(self):

        This function creates a new toplevel window that allows the
        user to enter arguments and options for the command and then
        actually run the command.
        """
        window = Tkinter.Toplevel()
        argFrame = Tkinter.Frame(window,relief='ridge',bd=3)
        buttonFrame = Tkinter.Frame(window)

        commandTitle=Tkinter.Label(window,text='Run '+self.command.cmdName,
                                   relief='ridge',padx=3,pady=3)
        self.MakeLabelsAndEntrysForAllArguments(argFrame)
        self.MakeBottomButtonsForGUICommand(buttonFrame,window)

        commandTitle.pack(side='top',fill='both',expand=1)
        argFrame.pack(side='top',fill='both',expand=1)
        buttonFrame.pack(side='top',fill='both',expand=1)

#
#  End functions to make a genric GUI command dialog
#
######################################################################        

def EmtpyP(arg):
    if (str == type(arg)):
        arg = arg.strip()
    return (None == arg or '' == arg)

def StartGUI():
    """
    StartGUI():

    This function creates the main DIBS GUI window and then enters the
    Tk event loop.  This function returns once the user kills/quits the
    main GUI.
    """
    tk = Tkinter.Tk()
    MakeMainDIBSWindow(tk)
    tk.mainloop()
