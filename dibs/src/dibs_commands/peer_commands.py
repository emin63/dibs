
import dibs_options, dibs_constants
from templates import *

def ComplainAboutBadPeerOptions(email,peer,remote_quota,local_quota,comment,
                                talk,listen,host,port):
    """
    Raise an exception if the add_peer or edit_peer options
    don't make sense.
    """

    if (talk == 'active' and (host == None)):
        raise Exception, ('Host arg must be given when setting '
                                  + 'talk method to active.')
    if (talk and not dibs_constants.talkMethods.count(talk)):
        raise Exception, ('Invalid talk method, options are ' +
                                  string.join(dibs_constants.talkMethods))
    if (listen and not dibs_constants.talkMethods.count(listen)):
        raise Exception, ('Invalid listen method, options are ' +
                              string.join(dibs_constants.talkMethods))



class ForgetPeerCmd(DIBSCommand):
    """
    Forget all the data we are storing for peer and send peer
    a message to that effect.
    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.RequiredArg('peer=',StringValidator(),"""
        Name of peer to forget.
        """)


    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        d.ForgetPeer(self['peer'])

        self.FinishDIBSCommand()


class AddPeerCmd(DIBSCommand):
    """
    Make an entry for a peer in the database.

`dibs.py add_peer --peer PEER --email EMAIL  --remote_quota
REMOTE_QUOTA --local_quota LOCAL_QUOTA  --comment  COMMENT --talk TALK
--host HOST  [ --port PORT ]'

`--peer PEER'
     Name of the GPG key for the peer specified as the email address of
     the GPG key.

`--email EMAIL'
     Email address of the peer.  Messages are sent to this address on
     certain types of errors.

`--remote_quota REMOTE_QUOTA'
     Amount of space in kilo-bytes that the peer will allow your client.

`--local_quota LOCAL_QUOTA'
     Amount of space in kilo-bytes that you will allow the peer on your
     client.

`--talk TALK'
     This must be one of `active', `passive', or `mail' and specifies
     how your client will communicate to the peer *Note Flexible
     Communication Modes::.  If you can directly connect to your peer
     (e.g., there are no intervening firewalls), then you should
     probably use `active' mode.


`--listen LISTEN'
     This must be one of `active', `passive', or `mail' and specifies
     how your client will receive communication from the peer *Note
     Flexible Communication Modes::.  If your peer can directly connect
     to you peer (e.g., there are no intervening firewalls), then you
     should probably use `active' mode.

`--host HOST'
     This specifies the name or IP address of the peer's host.

`--comment COMMENT'
     This specifies a string which serves as a comment for the peer.

`--port PORT'
     This specifies the port the peer will listen on for direct
     connections.  It is only used if TALK is `active'.  This is an
     optional argument, with a default value of 6363.


   The add_peer command is used to create an entry in the database for
trading files with a peer.  For example, if you wanted to trade files
with me where I store 1 MB for you and you store 5 MB for me you would
issue the command:

   `dibs.py add_peer --email emin@allegro.mit.edu --peer
emin.dibs@alum.mit.edu --local_quota 5000 --remote_quota 1000 --comment
``trade with emin'' --talk active --listen active --host martinian.com'

   A `k', `m', `g', or, `t' can be appended to a quota indicating that
the number should interpreted as kilo-bytes (the default if no letter
is appended), mega-bytes, giga-bytes, or tera-bytes.  For example, the
`--local_quota 5000' in the example above could be replaced by
`--local_quota 5M' NOT `--local_quota 5K'.
    
    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.RequiredArg('email=',StringValidator(),"""
        Email address of the peer. Messages are sent to this address on
        certain types of errors. 
        """)

        self.RequiredArg('peer=',StringValidator(),"""
        Name of the GPG key for the peer specified as the email address
        of the GPG key.
        """)

        self.RequiredArg('remote_quota=',FileSizeValidator(),"""
        Amount of space in kilo-bytes that the peer will allow your client.
        The abbreviations m, g, and t can also be used to specify a size
        in megabytes, gigabytes, and terabytes.
        """)

        self.RequiredArg('local_quota=',FileSizeValidator(),"""
        Amount of space in kilo-bytes that you will allow the peer on your
        client.  The abbreviations m, g, and t can also be used to specify
        a size in megabytes, gigabytes, and terabytes.
        """)

        self.RequiredArg('comment=',StringValidator(),"""
        This specifies a string which serves as a comment for the peer. 
        """)

        self.RequiredArg('talk=',StrictTalkTypeValidator(),"""
        This must be one of active or passive and specifies how your
        client will communicate to the peer.  If you can directly connect
        to your peer (e.g., there are no intervening firewalls), then you
        should use active mode.
        """)

        self.RequiredArg('listen=',StrictTalkTypeValidator(),"""
        This must be one of active or passive and specifies how your
        peer will communicate to your client.  If your peer will directly 
        connect to you (e.g., there are no intervening firewalls), then you
        should use active mode.        
        """)
                         

        self.OptionalArg('host=',StringValidator(),"""
        This specifies the name or IP address of the peer's host.  If
        --talk is active, then this argument is required, otherwise it is
        optional.
        """)

        self.OptionalArg('port=',IntegerValidator(0),"""
        This specifies the port of the peer's host.  If --talk is active,
        then this argument is required, otherwise it is optional.
        """)

    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        if (self['port']):
            self['port'] = int(self['port'])
        ComplainAboutBadPeerOptions(self['email'],self['peer'],
                                    self['remote_quota'],
                                    self['local_quota'],self['comment'],
                                    self['talk'],self['listen'],
                                    self['host'],self['port'])
        d.database.AddPeer(self['email'],self['peer'],self['remote_quota'],
                           self['local_quota'],self['comment'],
                           self['talk'],self['listen'],self['host'],
                           self['port'])

        self.FinishDIBSCommand()

class EditPeerCmd(DIBSCommand):
    """
    Change an existing entry in the database.
    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.OptionalArg('email=',StringValidator(),"""
        Email address of the peer. Messages are sent to this address on
        certain types of errors. 
        """)

        self.OptionalArg('peer=',StringValidator(),"""
        Name of the GPG key for the peer specified as the email address
        of the GPG key.
        """)

        self.OptionalArg('remote_quota=',FileSizeValidator(),"""
        Amount of space in kilo-bytes that the peer will allow your client.
        The abbreviations m, g, and t can also be used to specify a size
        in megabytes, gigabytes, and terabytes.
        """)

        self.OptionalArg('local_quota=',FileSizeValidator(),"""
        Amount of space in kilo-bytes that you will allow the peer on your
        client.  The abbreviations m, g, and t can also be used to specify
        a size in megabytes, gigabytes, and terabytes.
        """)

        self.OptionalArg('comment=',StringValidator(),"""
        This specifies a string which serves as a comment for the peer. 
        """)

        self.OptionalArg('talk=',StrictTalkTypeValidator(),"""
        This must be one of active or passive and specifies how your
        client will communicate to the peer.  
        """)

        self.OptionalArg('listen=',StrictTalkTypeValidator(),"""
        This must be one of active or passive and specifies how your
        peer will communicate to your client.  
        """)
                         
        self.OptionalArg('host=',StringValidator(),"""
        This specifies the name or IP address of the peer's host.  
        """)

        self.OptionalArg('port=',IntegerValidator(0),"""
        This specifies the port of the peer's host.  
        """)


    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)

        ComplainAboutBadPeerOptions(self['email'],self['peer'],
                                    self['remote_quota'],
                                    self['local_quota'],self['comment'],
                                    self['talk'],self['listen'],
                                    self['host'],self['port'])
        d.database.EditPeer(self['email'],self['peer'],self['remote_quota'],
                            self['local_quota'],self['comment'],
                            self['talk'],self['listen'],self['host']
                            ,self['port'])

        self.FinishDIBSCommand()


class DeletePeerCmd(DIBSCommand):
    """
    Remove a peer from the database.
    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)
        self.RequiredArg('peer=',StringValidator(),"""
        Name of peer to delete.
        """)
                         

    def run(self,argv=None,parentWindow=None):

        if (None != argv):
            self.ParseRequiredArgs(argv)

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        d.database.DeletePeer(self['peer'])

        self.FinishDIBSCommand()
