
import urllib, xml, xml.parsers, xml.parsers.expat
import time, string, random
import dibs_utils, dibs_constants


def MakeAttribute(nameValuePair):
    return nameValuePair[0] + '="' + `nameValuePair[1]` + '" '

class DIBSPostedContract:
    """
    The DIBSPostedContract class represents the data for a contract posted
    for other peers to trade data with the poster.

    Peers respond with DIBSProposal object.
    """

    def __init__(self,host=None,port=None,talkType=None,listenType=None,
                 pubKey=None,admin=None,minQuota=None,maxQuota=None,
                 quotaMultiplier=None,lifetime=None,name=None,
                 url=None):
        for item in ['host','port','minQuota','maxQuota','quotaMultiplier',
                     'lifetime','name']: # store some args in self
            self.__dict__[item] = locals()[item]
        self.peerTalkType = talkType # how poster talks to peer
        self.peerListenType = listenType # how poster listens to peer
        self.postDate = time.time()
        self.keyNameForContract = pubKey
        self.emailForContract = admin
        self.url = 'none' # gets updated if/when contract posted to url
        self.dibsVersion = None
        self.publicKey = None
        self.SetDefaults()
        if (not dibs_utils.EmptyP(url)):
            self.GetContractFromURL(url)
            self.revokePW = None
        else:
            self.revokePW = dibs_utils.HashToFileName(self.name +
                                                      `random.random()`)

    def SetDefaults(self):
        """
        Setup default values for things that have not been assigned.
        """

        defaultName = dibs_utils.HashToFileName(string.join(
            map(lambda x: `x`,[
            self.host,self.peerTalkType,self.peerListenType,
            self.minQuota,self.maxQuota,self.quotaMultiplier,
            self.lifetime,self.postDate,`random.random()`,
            self.keyNameForContract,self.emailForContract]),' '))
        
        for nameAndDefault in [('name',defaultName),('peerTalkType','any'),
                               ('peerListenType','any')]:
            if (dibs_utils.EmptyP(self.__dict__[nameAndDefault[0]])):
                self.__dict__[nameAndDefault[0]] = nameAndDefault[1]

    def __str__(self):
        return ('\t<POSTED_CONTRACT ' +
                string.join(map(MakeAttribute,(
            ('ID', self.name),('HOST',self.host),('PORT',self.port),
            ('URL', `self.url`),
            ('TALK_TYPE',self.peerTalkType),
            ('LISTEN_TYPE',self.peerListenType),('MIN_QUOTA',`self.minQuota`),
            ('MAX_QUOTA',`self.maxQuota`),
            ('QUOTA_MULT',`self.quotaMultiplier`),
            ('LIFETIME',`self.lifetime`),('POST_DATE',`self.postDate`),
            ('PUB_KEY_NAME',self.keyNameForContract),
            ('PUB_KEY',self.publicKey),
            ('EMAIL',self.emailForContract))),'\n\t\t') +
                '></POSTED_CONTRACT>')

    def GetPeerParams(self):
        return (self.host, self.port,
                self.emailForContract, self.keyNameForContract)

    def GetContractFromURL(self,url):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.StartElement
        self.parser.EndElementHandler = self.EndElement
        self.parser.CharacterDataHandler = self.ParseCharacterData
        self.currentTag = ''

        fullURL = 'http://' + url + '/' + 'contract_request.cgi'
        u = urllib.urlopen(fullURL,urllib.urlencode({'name':self.name}))
        data = u.read()
        if ('FAIL:' == string.strip(data)[0:5]):
            raise Exception, ('Could not get contract ' + self.name +
                              ' from url ' + fullURL)
        else:
            self.parser.Parse(data)
            self.publicKey = dibs_utils.RemovePGPHeaders(
                self.publicKey,dibs_constants.pgpKeyStart,
                dibs_constants.pgpKeyEnd)
            
    def StartElement(self,name,attrs):
        self.currentTag = name
        if ('POSTED_CONTRACT' == name):
            self.nextItemToParse = None
        elif ('ITEM' == name):
            if (not self.__dict__.has_key(attrs['id'])):
                raise Exception, 'Unexpected item id ' + attrs['id']
            self.nextItemToParse = attrs['id']
            self.__dict__[self.nextItemToParse] = ''

    def ParseCharacterData(self,data):
        if (None == self.nextItemToParse):
            pass
        else:
            self.__dict__[self.nextItemToParse] += data

    def EndElement(self,name):
        if (self.__dict__.has_key('nextItemToParse')):
            self.nextItemToParse = None
    
    def PostToContractServer(self,url,pubKey):

        paramDict = dict(self.__dict__)
        paramDict['publicKey'] = pubKey
        paramDict['dibsVersion'] = dibs_constants.version_string
        params = urllib.urlencode(paramDict)
        f = urllib.urlopen('http://' + url + '/post.cgi',params)
        result = f.read()
        f.close()
        self.url = url
        return result

    def UnpostToContractServer(self,url):

        paramDict = dict(self.__dict__)
        params = urllib.urlencode(paramDict)
        f = urllib.urlopen('http://' + url + '/unpost.cgi',params)
        return f.read()


class DIBSProposedContract:
    """
    The DIBSProposedContract class holds data for a contract we are
    proposing to the peer.  All the arguments (except peerHost,
    peerPort, peerEmail) are from the point of view of the recipient
    we are proposing the contract to.  For example, the talkType is
    what the peer would use as the argument to --talk and
    the proposedRemoteQuota is what the peer would use as the
    argument to --remote_quota in the add_peer function.
    """

    def __init__(self,contractName,localQuota,remoteQuota,
                 talk,listen,host,port,peerHost,peerPort,
                 peerEmail,pubKey,admin):
        self.contractName = contractName
        self.localQuota = localQuota
        self.remoteQuota = remoteQuota
        self.talk = talk
        self.listen = listen
        self.host = host
        self.port = port
        self.peerHost = peerHost
        self.peerPort = peerPort
        self.peerEmail = peerEmail
        self.proposalDate = time.time()
        self.keyNameForContract = pubKey
        self.emailForContract = admin
        
        if (dibs_utils.EmptyP(self.talk)):
            self.talk = 'active'
        if (dibs_utils.EmptyP(self.listen)):
            self.listen = 'active'

    def __str__(self):        
        return ('\t<PROPOSED_CONTRACT> ' +
                string.join(map(MakeAttribute,(
            ('ID', self.contractName),('LOCAL_QUOTA',`self.localQuota`),
            ('REMOTE_QUOTA',`self.remoteQuota`),('TALK',self.talk),
            ('LISTEN',self.listen),('HOST',self.host),('PORT',`self.port`),
            ('PEER_HOST',self.peerHost),('PEER_PORT',`self.peerPort`),
            ('PEER_EMAIL',self.peerEmail),
            ('DATE',`self.proposalDate`),
            ('PUB_KEY_NAME',self.keyNameForContract),
            ('EMAIL',self.emailForContract))),'\n\t\t')
                + '></PROPOSED_CONTRACT>')


            
