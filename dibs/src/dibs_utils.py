
"""
This file contains simple functions which do not depend on any
of the other dibs files (except dibs_constants.pyt) or
implementation details.
"""

import os, os.path
import time
import traceback
import sys
import md5
import binascii
import string
import re
import smtplib
import shutil

import dibs_constants

def PathJoin(a,b):
    """
    Take two path components a and b and join them appropriately.
    This function is needed because, on UNIX, paths are joined
    using a forward slash while on windows they are joined with
    a backward slash.  We don't use the builtin os.path.join
    function because that won't join absolute paths which
    we sometimes need to do.
    """
    if (os.path.isabs(b)):
        return a + os.sep + b.replace(':','@@colon@@')
    else:
        return a + os.sep + b


def MailDataToUser(data,fromAddress,emailAddress,smtpServer,safe=0):
    """
    Emails data to user.

    If an exception occurs, and safe is true, then the exception is
    caught and a message describing the error is returned.  If safe is
    false, then the exception is re-raised and passed up.

    If no error occurs, the empty string is returned.
    """

    try:
        server = smtplib.SMTP(smtpServer)
        server.sendmail(fromAddress,emailAddress,data)
        return ''
    except Exception, e:
        if (safe):
            msg = ('Could not send message from ' + fromAddress +
                   ' to ' + emailAddress + ' because of exception:\n\n' + `e`)
            return msg
        else:
            raise e


def MailErrorMsgToUser(msg,fromAddr,emailAddr,warnLevel,maxLevel,logMsgDir,
                       smtpServer):
    """
    MailErrorMsgToUser(msg,fromAddr,emailAddr,warnLevel,maxLevel,logMsgDir,
                       smtpServer)

    This functions saves msg in logMsgDir.  If there are more than warnLevel
    messages in that directory, the user is warned that the directory is
    filling up.  If there are less than maxLevel messages in that dir then
    msg is emailed to the address emailAddr from the address fromAddr.
    """
    try:
        WriteToFile(msg,PathJoin(logMsgDir,'error_') + `time.time()`)
        count = len(os.listdir(logMsgDir))
        if (count > maxLevel):
            return ('Could not send message to user; '+
                    'too many messages pending.')
        if (count > warnLevel):
            warnMsg = 'Subject: DIBS WARNING\n\n'
            warnMsg = warnMsg + (
                'Warning: There are currently ' + `count` +
                ' messages waiting to be\n' +
                'read and removed in the directory ' + logMsgDir +
                '.\n\nOnce there are ' + `maxLevel` +
                ' uncleared messages, you will no\n' +
                'longer be notified of errors my email.\n')
            MailDataToUser(warnMsg,fromAddr,emailAddr,smtpServer)
        return MailDataToUser(msg,fromAddr,emailAddr,smtpServer,1)
    except Exception, e:
        msg =  ('Could not send message from ' + fromAddr +
                ' to ' + emailAddr + ' because of exception:\n\n' + `e`)
        print msg
        return msg
            


def WriteToFile(data,fname):
    "Dump data to fname.  Any intervening directories required are created"

    assert len(fname) < 1000
    dir = os.path.dirname(fname)
    if (not os.path.exists(dir)):
        os.makedirs(dir)
    fd = open(fname,'wU')
    fd.write(data)
    fd.close()

def GetTracebackString(exc_info):
    s = 'Traceback:\n'
    for line in traceback.format_tb(exc_info[2]):
        s = s + line
    return s

def HashFile(fileName):
    m = md5.new()
    fd = open(fileName,'rU')
    data = 'start'
    while( data ):
        data = fd.read(65536)
        m.update(data)
    fd.close()
    return binascii.b2a_base64(m.digest())
    
def HashString(str):
    "Return md5 hash of str."
    return binascii.b2a_base64(md5.new(str).digest())[0:22]

def HashStringNoB2A(str):
    "Return md5 hash of str in binary."
    return md5.new(str).digest()

def HashToFileName(str):
    """
    Return md5 hash of str with / converted to S so that the result
    can be used as a file name.
    """
    return string.replace(binascii.b2a_base64(md5.new(str).digest())[0:22],
                          '/','S')
def GetModTime(file):
    return os.stat(file)[8]

def MoveFile(src,dst):
    """
    Python doesn't have a working move file command (the rename command
    fails if src and dst are on different partitions), so implement our own.
    """
    shutil.copy(src,dst)
    os.unlink(src)

def DeleteEmptyDirs(dir):
    """
    Delete all emtpy directories in dir.  Afterwards, if dir
    is emtpy, delete it and return 0, else return 1.
    """
    for item in os.listdir(dir):
        dirName = PathJoin(dir,item)
        if (os.path.isdir(dirName)):
            if (DeleteEmptyDirs(dirName)):
                return 1
        else:
            return 1
    os.rmdir(dir)
    return 0

def Quote(str):
    return '"' + str + '"'

def MailUserIfLockfileTooOld(lockfileName,admin,smtpServer):
    diff = time.time() - GetModTime(lockfileName)
    if (diff > 86400):
        MailDataToUser('WARNING: lockfile ' + lockfileName +
                       ' seems old and prevents dibs operations.\n' +
                       'If this lockfile is stale, please remove it.\n',
                       admin,admin,smtpServer)

def RemovePGPHeaders(data,startHeader=dibs_constants.pgpMsgStart,
                     endHeader=dibs_constants.pgpMsgEnd):
    startLength = len(startHeader)
    endLength = len(endHeader)
    assert startHeader == data[0:startLength], (
        'data did not start with pgp header ' + `startHeader`)
    assert endHeader == data[(len(data)-endLength):len(data)], (
        'data did not end with pgp header ' + `endHeader`)
    return data[startLength:(len(data)-endLength)]

def AddPGPHeaders(data):
    return string.join([dibs_constants.pgpMsgStart,data,
                        dibs_constants.pgpMsgEnd],'')
        
def EmptyP(arg):
    return None == arg or (str == type(arg) and '' == arg.strip())
