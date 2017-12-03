#!/usr/bin/python


import string, sys, re, os, os.path
import xml, xml.parsers, xml.parsers.expat
import cgi
import cgitb; cgitb.enable() # put error messages into httpd error log

from dibs_lib.peer_finder import dibs_pf_options
from dibs_lib import dibs_constants

contractNameRE = re.compile('^[0-9a-zA-Z_+@.]+$')
goodCharsRE = re.compile('^[0-9a-zA-Z_+@.]+$')

def SaveContract(name,revokePW,data):
    """
    Save the contract in dibs_pf_options.storageDir.

    name:     Name of contract
    revokePW: Revocation password for contract.
    data:     Data for the contract.
    """
    storageFile = os.path.join(dibs_pf_options.storageDir,name)
    if (os.path.exists(storageFile)):
        raise Exception, 'Contract by that name already exists.'
    elif (len(os.listdir(dibs_pf_options.storageDir)) >
          dibs_pf_options.maxContracts):
        raise Exception, 'Too many contracts'
    else:
        fd = open(storageFile, 'w')
        fd.write(data)
        fd.close()
        fd = open(os.path.join(dibs_pf_options.revokePWDir,name), 'w')
        fd.write(revokePW)
        fd.close()

def RevokeContract(name,revokePW):
    """
    Revoke a contract and remove it from the contract server.

    name:     Name of the contract to revoke.
    revokePW: Revocation password given when contract was created and
              stored in dibs_pf_options.revokePWDir.
    """
    fd = open(os.path.join(dibs_pf_options.revokePWDir,name), 'r')
    truePW = fd.read()
    fd.close()
    if (not string.strip(revokePW) == string.strip(truePW)):
        raise Exception, 'Wrong revoke password'
    else:
        os.remove(os.path.join(dibs_pf_options.storageDir,name))
            
def ComplainIfContractNameHasBadChars(contractName):
    if (not contractNameRE.match(contractName)):
        raise Exception, 'Bad characters in contract name'

def ComplainIfFieldHasBadChars(fieldName,fieldValue):
    strippedFieldValue = str(fieldValue)
    strippedFieldValue = strippedFieldValue.strip('\'')
    if (not goodCharsRE.match(strippedFieldValue)):
        raise Exception, 'Bad characters in field %s=%s name' % (
	    fieldName,strippedFieldValue)

def ValidCommType(s):
    if (['passive','active','any'].count(s) <= 0):
        raise Exception, 'Bad communication type; must be any/passive/active.'
    else:
        return s
    
def ProcessPostRequest():
    """
    Process a post contract request.  Reads the required data for
    the contract from the HTTP POST request and saves it in a file
    in dibs_pf_options.storageDir and dibs_pf_options.revokePWDir.
    """

    contractData = ['<POSTED_CONTRACT>']

    try:

        form = cgi.FieldStorage()

        for (fieldName,fancyName,fieldType) in (
            ('name','Contract Name',str),
            ('minQuota','Minimum Quota',int),('maxQuota','Maximum Quota',int),
            ('quotaMultiplier','Quota Multiplier',float),
            ('peerTalkType','Talk Type',ValidCommType),
            ('peerListenType','Listen Type',ValidCommType),
            ('host','Host',str),('port','Port',str),
            ('emailForContract','Email',str),
            ('dibsVersion','DIBS Version',str),
            ('keyNameForContract','Public Key Name',str),
            ('publicKey','Public Key',str),
            ('postDate','Post Date',float),
            ('lifetime','Lifetime',float)):
            fieldValue = fieldType(form[fieldName].value)
            if (str != fieldType):
                fieldValue = `fieldValue`
	    if (fieldName != 'publicKey'):
		ComplainIfFieldHasBadChars(fieldName,fieldValue)

            contractData.append('<ITEM id="' + fieldName + '" title="' +
                                fancyName + '">' + fieldValue + '</ITEM>\n')

        contractData.append('</POSTED_CONTRACT>')
        revokePW = form['revokePW'].value
        contractName = form['name'].value
        ComplainIfContractNameHasBadChars(contractName)

        SaveContract(contractName,revokePW,string.join(contractData,'\n'))
        
    except Exception, e:
        return ('FAIL\n\n' + e.__str__())
    
    return 'OK'

def ProcessRevokeRequest():
    """
    Process a contract revocation request.
    """

    try:

        form = cgi.FieldStorage()

        revokePW = form['revokePW'].value
        contractName = form['name'].value
        ComplainIfContractNameHasBadChars(contractName)

        RevokeContract(contractName,revokePW)
        
    except Exception, e:
        return ('FAIL\n\n' + e.__str__())
    
    return 'OK'


class ContractPrettyPrinter:
    """
    Class used to read in a contract stored in XML format and
    produce HTML to display the contract info.
    """
    def __init__(self,data):
        self.parser = xml.parsers.expat.ParserCreate()
        self.parser.StartElementHandler = self.StartElement
        self.parser.EndElementHandler = self.EndElement
        self.parser.CharacterDataHandler = self.ParseCharacterData        
        self.output = []
        self.parser.Parse(data)

    def GetPrettyContract(self):
        return string.join(self.output)

    def StartElement(self,name,attrs):
        if ('ITEM' == name):
            self.output.append('<TR><TD>' + attrs['title'] + '</TD><TD><PRE>')
        elif ('POSTED_CONTRACT' == name):
            self.output.append('<TABLE>')
        else:
            raise Exception, 'Unexpected start tag "' + name + '" seen.'

    def ParseCharacterData(self,data):
        self.output.append(data)
        
    def EndElement(self,name):
        if ('ITEM' == name):
            self.output.append('</PRE></TD></TR>')
        elif ('POSTED_CONTRACT' == name):
            self.output.append('</TABLE>')
        else:
            raise Exception, 'Unexpected end tag "' + name + '" seen.' 

def ShowContracts():
    files = os.listdir(dibs_pf_options.storageDir)
    result = ['There are currently ' + `len(files)` + ' contracts posted.<hr>']
    for file in files:
        fd = open(os.path.join(dibs_pf_options.storageDir,file),'r')
        p = ContractPrettyPrinter(fd.read())
        result.append(p.GetPrettyContract())
        result.append('<HR>')                
        fd.close()

    return string.join(result,'\n')


def ProcessContractRequest():

    try:

        form = cgi.FieldStorage()

        contractName = form['name'].value
        ComplainIfContractNameHasBadChars(contractName)
        fileName = os.path.join(dibs_pf_options.storageDir,contractName)
        if (os.path.exists(fileName)):
            fd = open(fileName,'r')
            return (fd.read())
        else:
            raise Exception, 'unknown contract ' + contractName
        
    except Exception, e:
        return 'FAIL:\n\n' + e.__str__()

def ContractServerInfoString():
    return string.join([
        '<hr>'
        'This contract server is administered by ',dibs_pf_options.admin,
        '<BR>',
        'The <a href="http://dibs.sourceforge.net">',
        'Distributed Internet Backup System (DIBS)','</a>',
        'can be downloaded <A href="http://sourceforge.net/projects/dibs">',
        '<IMG src="http://sourceforge.net/sflogo.php?group_id=69007&amp;type=5" width="210" height="62" border="0" alt="SourceForge"></A>'],'\n')

def MakeTaggedString(tag,str):
    return '<'+tag+'>'+str+'</'+tag+'>'

def ShowContractServerUsage():


    titleStr = ('DIBS Peer Finding Service (Version ' +
                dibs_constants.version_string + ')')

    usageStr = """
    This contract server is used to find peers to trade data with
    using DIBS.  See the
    <a href='http://sourceforge.net/docman/?group_id=69007>documentation</a>
    for details.
    """

    msg = string.join([
        MakeTaggedString('TITLE',titleStr),
        MakeTaggedString('CENTER',MakeTaggedString('H1',titleStr)),usageStr,
        ContractServerInfoString()],'\n')

    return msg
