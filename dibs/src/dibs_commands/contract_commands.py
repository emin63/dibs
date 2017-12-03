
import time
import dibs_options
from templates import *

class PostPeerContractCmd(DIBSCommand):
    """
    The `post_contract' command posts an advertisement for a trading
    contract to a server.  Someone else can then propose a specific
    contract matching the posted parameters using the
    `propose_contract' command.  If the contract is accepted, then GPG
    keys are exchanged and the appropriate modifications are made to
    the database of the poster and proposer without the need to
    manually use the `add_peer' or `edit_peer' commands.

    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)
        
        self.RequiredArg('min_quota=',FileSizeValidator(),"""
        The minimum quota the poster wants a potential peer to provide.
        By default, space is specified in kilo-bytes, but m, g, or t can
        be appended to a number to indicate megabytes, gigabytes, or
        terabytes (e.g., 10m for 10 megabytes).""")
        
        self.RequiredArg('max_quota=',FileSizeValidator(),"""
        The maximum quota the poster wants a potential peer to provide
        specified in the format as for MIN_QUOTA.""")
        
        self.RequiredArg('quota_mult=',FloatValidator(0.0),"""
        The minimum ratio of space that the potential peer will provide to the
        space the potential peer will receive in return from the poster.""")
                         
        self.RequiredArg('lifetime=',IntegerValidator(0),
                         'Amount of time (in seconds) to post contract for')
        
        self.OptionalArg('url=',StringValidator(),"""
        The URL to post the contract to. If no URL is provided then the value
        of the defaultContractServerURL will be used. Also, if --url none is
        specified, then the contract is not posted to any contract server.
        Using the post_contract command and not posting the contract to any
        URL is pointless, but this can be useful for testing purposes.""")
        
        self.OptionalArg('host=',StringValidator(),"""
        The host name of the poster's DIBS client. By default, this is
        obtained from the hostname variable and should not need to be
        specified on the command line except in special situations.""")
        
        self.OptionalArg('contract_name=',StringValidator(),"""
        Specifies a name for the contract. By default, a name is
        automatically generated for each contract. Usually using the
        default name is best and there is no need to explicitly specify a
        name. Occasions where you would want to explicitly specify a name
        include if you want to be able to ask a friend or associate to
        respond to a particular contract you posted specifically for him
        or if you are using DIBS in automated scripts.""")
        
        self.OptionalArg('port=',IntegerValidator(0),"""
        The port where the poster's DIBS daemon will be listening for
        connections. By defualt, this is obtained from the daemonPort
        variable and should not need to specified on the command line
        except in special situations.""")
        
        self.OptionalArg('talk=',TalkTypeValidator(),"""
        Must be one of active, passive, or any and specifies the talk mode
        the poster will use in communicating with the potential peer if
        the contract is accepted.""")
        
        self.OptionalArg('listen=',TalkTypeValidator(),"""
        Must be one of active, passive, or any and specifies the listen mode
        the poster will use receiving communications from the potential peer
        if the contract is accepted.""")

    def run(self,argv=None,parentWindow=None):

        self.PrepareForDIBSCommand()
        
        if (None != argv):
            self.ParseRequiredArgs(argv)
        self.WarnAboutLocalhostHostIfNecessary()
        if (not self['port']):
            self['port'] = dibs_options.daemonPort
        self.ComplainAboutMissingRequiredArguments()

        import dibs_main
        d = dibs_main.DIBS(self.database)
        if (not self['url']):
            self['url'] = dibs_options.defaultContractServerURL
        d.PostPeerContract(self['host'],self['port'],
                           self['talk'],self['listen'],
                           self['min_quota'],self['max_quota'],
                           self['quota_mult'],self['lifetime'],
                           self['contract_name'],self['url'])

        self.FinishDIBSCommand()

class UnpostPeerContractCmd(DIBSCommand):

    """
    This command unposts the contract with name CONTRACT_NAME previously
    posted with post_contract.  By default, the URL to unpost from
    is obtained from the defaultContractServerURL variable and
    should not need to be specified.

    Also, if `--url none' is specified then the named contract is
    removed from the DIBS database but the contract server is not
    contacted.  Generally this would be a bad idea, but it can be
    useful if contract server has removed (or never received) the
    contract in question and you now want to remove the contract from
    your DIBS database.

    """
    
    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.RequiredArg('contract_name=',StringValidator(),"""
        Name of the contract to revoke.  Use the command
        
          show_database --only posted_contracts

        to see the posted contracts in your database.
        """)

        self.OptionalArg('url=',StringValidator(),"""
        The URL to post the contract to. If no URL is provided then the
        value of the defaultContractServerURL variable will be used.
        Also, if --url none is specified then the named contract is removed
        from the DIBS database but the contract server is not contacted.
        Generally this would be a bad idea, but it can be useful if contract
        server has removed (or never received) the contract in question and
        you now want to remove the contract from your DIBS database.
        """)

    def run(self,argv=None,parentWindow=None):
        self.PrepareForDIBSCommand()

        if (None != argv):
            self.ParseRequiredArgs(argv)

        import dibs_main
        d = dibs_main.DIBS(self.database)
        if (None == self['url'] or '' == self['url'].strip()):
            self['url'] = dibs_options.defaultContractServerURL
        d.UnpostPeerContract(self['contract_name'],self['url'])

        self.FinishDIBSCommand()

class ProposePeerContractCmd(DIBSCommand):
    """
    Propose acceptance of a contract posted by the peer.

    All parameters are from the perspective of what the peer should
    issue in its add_peer command except for peer_host and peer_port
    which describe how to contact the peer.

    The `propose_contract' command proposes a specific contract within
    the parameters of the posted contract specified by CONTRACT_NAME.
    Specifically, if the poster accepts incoming connections, the
    proposer's DIBS client will attempt to contact the poster.

    Once contacted, the poster will examine the proposed contract and
    respond with an automated email to the proposer describing its
    decision.  If the proposed contract is accepted by the poster,
    then the poster will attempt to contact the proposer's DIBS client
    to exchange GPG keys, and enter the trading relationship in each
    client's database.

    Thus if both poster and proposer accept incoming connections, the
    trading relationship should be automatically established and
    trading will commence as usual.  If either the poster or proposer
    is behind a firewall and requires passive mode, things are more
    complicated.

    If the proposer is behind a firewall and cannot accept incoming
    connections, then it will not be able to obtain the poster's
    response to a proposal until it issues a `poll_passives' command
    and followed by a `process_message' command to the poster.  The
    DIBS daemon should eventually do this automatically, but the
    impatient user may wish to manually issue these commands after a
    contract is proposed.

    If the poster is behind a firewall and cannot accept incoming
    connections, then things are even more complicated.  In this case,
    there is no way that the proposer can contact the poster to
    initiate a proposal.  Thus, posting a contract for a DIBS client
    which cannot accept incoming connections because it is behind a
    firewall is generally not a good idea.

    """

    def __init__(self,cmdName):
        DIBSCommand.__init__(self,cmdName)

        self.RequiredArg('contract_name=',StringValidator(),"""
        Name of the contract the proposer is responding to.  This should be the
        name displayed on the peer finder service the contract is posted on.
        """)

        self.RequiredArg('local_quota=',FileSizeValidator(),"""
        Amount of space the poster will allow for the proposer, i.e., this
        is equivalent to what the poster would enter as the
        --local_quota argument if he were to use the add_peer command to
        implement the proposed contract.  If you are proposing a contract,
        you are the proposer (the poster is the person who posted the
        contract).  Therefore the local_quota argument in this context
        is how much space the other person will store for you.

        By default, space is specified in kilo-bytes, but m, g, or t can
        be appended to a number to indicate megabytes, gigabytes, or
        terabytes (e.g., 10m for 10 megabytes).
        """)

        self.RequiredArg('remote_quota=',FileSizeValidator(),"""
        Amount of space the proposer will get from the poster, i.e., this
        is equivalent to what the poster would enter as the
        --remote_quota argument if he were to use the add_peer command to
        implement the proposed contract.  If you are proposing a contract,
        you are the proposer (the poster is the person who posted the
        contract).  Therefore the remote_quota argument in this context
        is how much space you will store for the other person.

        By default, space is specified in kilo-bytes, but m, g, or t can
        be appended to a number to indicate megabytes, gigabytes, or
        terabytes (e.g., 10m for 10 megabytes).
        """)

        self.OptionalArg('auto_poll',YesNoValidator('yes'),"""
        Whether or not to issue a poll_passives and process_message command
        immediately after the proposal.  If you are behind a firewall, you
        will definetly need to poll the poster to get his response.
        """)

        self.OptionalArg('talk=',StrictTalkTypeValidator('passive'),"""
        The method the poster should use to communicate to the proposer, i.e.,
        this is equivalent to what the poster would enter as the --talk
        argument if he were to use the add_peer command to implement the
        proposed contract. If this is not provided, then it is obtained
        from the posted contract.         
        """)

        self.OptionalArg('listen=',StrictTalkTypeValidator('active'),"""
        The method the proposer will use to communicate to the poster, i.e.,
        this is equivalent to what the poster would enter as the --listen
        argument if he were to use the add_peer command to implement the
        proposed contract. If this is not provided, then it is obtained from
        the posted contract.
        """)

        self.OptionalArg('url=',StringValidator(),"""
        The URL to post the contract to. If no URL is provided then the
        value of the defaultContractServerURL variable will be used.
        """)

        self.OptionalArg('host=',StringValidator(),"""
        The name of the machine for the proposer's DIBS client, i.e., this is
        equivalent to what the poster would enter as the --host argument if he
        were to use the add_peer command to implement the proposed contract.
        Usually this is obtained from the contract and should not be specified.
        """)

        self.OptionalArg('peer=',StringValidator(),"""
        The name of the GPG key for the peer, i.e., this is equivalent to
        what the poster would enter as the --peer argument if he were to use
        the add_peer command to implement the proposed contract. Usually this
        is obtained from the contract and should not be specified.         
        """)

        self.OptionalArg('peer_host=',StringValidator(),"""
        The name of the host for the poster's DIBS client. Usually, this is
        obtained form the posted contract information and should not need
        to be specified directly.
        """)

        self.OptionalArg('peer_port=',IntegerValidator(0),"""
        The port where the poster's DIBS client listens for incoming
        connections. Usually, this is obtained form the posted contract
        information and should not need to be specified directly.
        """)

        self.OptionalArg('peer_email=',StringValidator(),"""
        The email address to use in contacting the poster. Usually, this is
        obtained form the posted contract information and should not need to
        be specified directly.
        """)        

    def run(self,argv=None,parentWindow=None):
        self.PrepareForDIBSCommand()

        if (None != argv):
            self.ParseRequiredArgs(argv)
            
        self.WarnAboutLocalhostHostIfNecessary()
        import dibs_main
        d = dibs_main.DIBS(self.database)

        d.ProposePeerContract(
            self['contract_name'],self['local_quota'],self['remote_quota'],
            self['talk'],self['listen'],self['host'],self['peer'],
            self['peer_host'],self['peer_port'],self['peer_email'],self['url'])

        if (str == type(self['auto_poll'])):
            self['auto_poll'] = self['auto_poll'].strip().lower()
        if (not ['','0','no',None,0].count(self['auto_poll'])):
            time.sleep(2)
            import communication_commands
            communication_commands.PollPassivesCmd('poll_passives').run(
                ['fake'])
            communication_commands.ProcessMessageCmd('process_message').run(
                ['fake'])

            
        self.FinishDIBSCommand()
