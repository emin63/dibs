
import os, tempfile
from dibs_mod_commands import getstatusoutput

import dibs_logger
import dibs_options

from dibs_utils import *
from dibs_exceptions import *

def DecryptFileToFile(fileOne,fileTwo):
    """
    Take fileOne, decrypt it, and store the result in fileTwo.
    If fileTwo exists, then it is not overwritten, but a warning
    is generated.
    """

    if (not os.path.exists(fileTwo)):
        cmdString = (dibs_options.gpgProg + ' --output '
                     + Quote(fileTwo)
                     + ' --decrypt ' + Quote(fileOne))
        [status,output] = getstatusoutput(cmdString)

        if (status):
            msg = ('DecryptFileToFile ' + fileOne + ' returned ' +
                   `status`  + ': ' + output + '\n'  + '\n' +
                   'Command was "' + cmdString + '"\n')
            raise DIBSException, msg
    else:
        dibs_logger.Logger.PrintAndLog(string.join(
            ['Not creating file ',fileTwo,' because it already exists.'],
            ''),dibs_logger.LOG_WARNING)

def MakeSignCmd(file,cipherFile,recipient):
    assert not EmptyP(recipient), (
        'No receipient for encryption. Did you specify GPG keys in dibsrc.py?')
    return (dibs_options.gpgProg + ' --batch -u ' +
            dibs_options.dibsPublicKey + ' --armor --clearsign -r '
            + recipient + ' -o ' + cipherFile + ' ' + Quote(file))

def MakeEncryptCmd(file,cipherFile,recipient):
    assert not EmptyP(recipient), (
        'No receipient for encryption. Did you specify GPG keys in dibsrc.py?')
    return (dibs_options.gpgProg + ' --always-trust --batch ' +
            ' --armor --encrypt -r ' +
            recipient + ' -o ' + Quote(cipherFile)
            + ' ' + Quote(file))

def MakeVerifyCmd(file):
    return (dibs_options.gpgProg + ' --batch -u ' +
            dibs_options.dibsPublicKey + ' --armor --verify '
            + Quote(file))

def MakeGetPubKeyCmd(junk,file,evenMoreJunk):
    return (dibs_options.gpgProg + ' --batch --armor --output '
            + file + ' --export ' + dibs_options.dibsPublicKey)

def GetPubKey():
    return CryptPiece('<empty>',MakeGetPubKeyCmd,'<empty>')
    

def SignPiece(piece,recipient):
    "Sign piece with key and return result."
    return CryptPiece(piece,MakeSignCmd,recipient)

def EncryptPiece(piece,keyName):
    """
    Encrypt piece with keyName.
    """
    return CryptPiece(piece,MakeEncryptCmd,keyName)

def EncryptToSelf(data):
    """
    Encrypt the input string to ourselves and return the result
    with the begin/end pgp message stuff removed.
    """
    return RemovePGPHeaders(
        CryptPiece(data,MakeEncryptCmd,dibs_options.dibsPrivateKey))

def DecryptFromSelf(data):
    """
    Decrypt the input string (which was encrypted by EncryptToSelf)
    and return the result.
    """
    encData = AddPGPHeaders(data)
    tempFileEnc = tempfile.mktemp()
    tempFileDec = tempfile.mktemp()
    fd = open(tempFileEnc,'wU') 
    fd.write(encData)
    fd.close()
    DecryptFileToFile(tempFileEnc,tempFileDec)
    fd = open(tempFileDec,'rU')
    decData = fd.read()
    fd.close()
    os.remove(tempFileEnc)
    os.remove(tempFileDec)

    return decData
    

def CryptPiece(piece,cryptCommand,recipient):
    "Encrypt or sign piece with dibs key and returns result."

    pieceFileName = tempfile.mktemp()
    WriteToFile(piece,pieceFileName)

    cryptFile = tempfile.mktemp()
    cmdString = cryptCommand(pieceFileName,cryptFile,recipient)

    dibs_logger.Logger.PrintAndLog('Executing crypto command:\n' + cmdString,
                                   dibs_logger.LOG_DEBUG)
    
    [status,output] = getstatusoutput(cmdString)
   
    os.remove(pieceFileName)

    if (status):
        msg = 'Crypting ' + pieceFileName + ' returned ' + `status`
        msg = msg + ': ' + output + '\n'
        msg = msg + '\n' + 'Command was "' + cmdString + '"\n'
        raise DIBSException, msg
    else:
        fd = open(cryptFile,'rU')
        result = fd.read()
        fd.close()
        os.remove(cryptFile)
        assert not os.path.exists(cryptFile), ('Could not remove file '
                                               + cryptFile)
        if (os.linesep != '\n'):
            result.replace(os.linesep,'\n')
        return result

def IsPubKeyUnknownP(keyName):
    cmd = dibs_options.gpgProg + ' --batch --list-keys ' + keyName
    (s,o) = getstatusoutput(cmd)
    return s

def GetKey(keyName):
    file = tempfile.mktemp()
    cmd = (dibs_options.gpgProg + ' --batch --armor --output ' + file
           + ' --export ' + keyName)
    (s,o) = getstatusoutput(cmd)
    if (s):
        msg = ('Getting key ' + `keyName` + 'in file ' +
               `file` + 'failed with output:\n' + o +
               '\n\n Command was ' + `cmd` + '\n')
        raise DIBSException, msg
    elif(not os.path.exists(file)):
        raise DIBSException, (
            'Exporting key ' + `keyName` + 'failed.\nDid you set ' +
            'dibsPublicKey and dibsPrivateKey correctly in your dibsrc.py?.')
    else:
        fd = open(file,'r')
        result = fd.read()
        fd.close()
        os.remove(file)
        return result

def ImportPublicKeyIfNecessary(keyName,keyData):
    if (IsPubKeyUnknownP(keyName)):
        file = tempfile.mktemp()
        WriteToFile(dibs_constants.pgpKeyStart + keyData +
                    dibs_constants.pgpKeyEnd,file)
        cmd = dibs_options.gpgProg + ' --batch --import ' + file
        (s,o) = getstatusoutput(cmd)
        if (s):
            msg = ('Importing public key ' + `keyName` + 'in file ' +
                   `file` + 'failed with output:\n' + o +
                   '\n\n Command was ' + `cmd` + '\n')
            raise DIBSException, msg
        else:
            os.remove(file)            

    
