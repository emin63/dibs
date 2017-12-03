
"""
This module contains the basic templates used to create DIBS command
objects.
"""

import string
import re
import sys
import os, os.path
import time
import tempfile
from getopt import getopt

try:
    import Tkinter
except:
    print 'Warning: Unable to import Tkinter.  GUI will be unvailable.'

import dibs_options

class DIBSCommand:
    """
    The DIBSCommand class is the basic template used to create all other
    command classes.  Every DIBS command should be defined by creating
    a new sublcass of DIBSCommand, defining the necessary required and
    optional arguments, and defining its Run method.  See the documentation
    for the run method in DIBSCommand for a discussion of how to
    override the default run method and write your own.

    See some of the examples in the dibs_command directory for usage.
    """
    
    def __init__(self,cmdName):
        """
        __init__(self,cmdName,requiredArgs,optionalArgs):

        cmdName:  A string representing the name of the command.
        
        """

        self.cmdName = cmdName
        
        self.argDict = {} # When the user enters arguments, they will
        # eventually be put into this dictionary.  Elements of argDict
        # should be accessed via the __get/setitem__ methods are [] operator.

        self.orderedRequiredArgs = [] # This will contain a list of required
        # arguments names (as strings) in order they should appear in the GUI.
        
        self.orderedOptionalArgs = [] # This will contain a list of optional
        # arguments names (as strings) in order they should appear in the GUI.
        
        self.arguments = {} # This dictionary will have the argument names
        # as keys and a dicitonary of argument properties as values.  For
        # example, the validator and doc string will go in here.

    def __getitem__(self,argName):
        """
        __getitem__(self,argName):

        Get the value of the argument with the given argName.
        """
        return self.argDict[argName]

    def __setitem__(self,argName,argVal):
        """
        __setitem__(self,argName):

        Set the value of the argument with the given argName.
        """        
        self.argDict[argName] = argVal
        return self.argDict[argName]

    def run(self,argv=None,parentWindow=None):
        """
        run(self,argv=None):

        argv:  Either None or an argv list indicated the arguments for
               this command as a list of strings with argv[0] being the
               program name.  If argv is not None, then the
               ParseRequiredArgs function should be called to parse argv,
               otherwise, the values of self.argDict[...] should already
               have been set (e.g., by the GUI).

        parentWindow:  Either None or a window from Tkinter indicating
                       the parent window of this command if this command
                       was invoked from the GUI.

        A command's run method should first call the PrepareForDIBSCommand
        function, then implement the desired functions, and finally call
        FinishDIBSCommand.  The return value should either be None or
        a string describing the result of running the command.  Any such
        strings returned will be displayed in a dialog box by the GUI.
        """
        if (None != argv):
            self.ParseRequiredArgs(argv)                

        self.PrepareForDIBSCommand()

        import dibs_main
        d = dibs_main.DIBS(self.database)

        # do whatever you like here
        result = 'Generic command called.'

        self.FinishDIBSCommand()

        return result

            
    def RequiredArg(self,fullName,validator,doc=None):
        """
        RequiredArg(self,fullName,validator,doc=None):

        fullName:  Name of the argument with an = appended if further values
                   can be given.  For example, an argument like --size 10
                   would have fullName='size='.

        validator: An instance of the Validator class to be used in validating
                   the input.

        doc:       A string representing documentation for the argument.

        This function specifies that a required argument along with some
        information about that argument.
        """
        name = self.StripEq(fullName)
        assert not self.arguments.has_key(name)
        self.orderedRequiredArgs.append(name)
        self.arguments[name] = {}
        self.arguments[name]['validator'] = validator
        self.arguments[name]['doc'] = doc
        self.arguments[name]['takes_args'] =('='==fullName[len(fullName)-1])
        
    def OptionalArg(self,fullName,validator,doc=None):
        """
        OptionalArg(self,fullName,validator,doc=None):

        fullName:  Name of the argument with an = appended if further values
                   can be given.  For example, an argument like --size 10
                   would have fullName='size='.

        validator: An instance of the Validator class to be used in validating
                   the input.

        doc:       A string representing documentation for the argument.

        This function specifies that an optional argument along with some
        information about that argument.
        """        
        name = self.StripEq(fullName)        
        assert not self.arguments.has_key(name)
        self.orderedOptionalArgs.append(name)
        self.arguments[name] = {}
        self.arguments[name]['validator'] = validator
        self.arguments[name]['doc'] = doc
        self.arguments[name]['takes_args'] =('='==fullName[len(fullName)-1])
        
    def has_key(self,k):
        return self.argDict.has_key(k)

    def StripEq(self,str):
        L = len(str)
        if (str[L-1] == '='):
            str = str[0:(L-1)]
        return str


    def ParseRequiredArgs(self,argv):
        """
        ParseRequiredArgs(self,argv):

        argv:  An argv structure suitable for the getopt module.
        
        This function parse through the argv to find the required and
        optional arguments and validates the arguments it finds using
        the self.argDict[arg]['validator'] for each arg.

        IMPORTANT NOTE:  You can either do the argument parsing/validation
        manually as done in the dibs_gui.py module OR you can call this
        function but you should not do both.  Specifically, some of the
        validators like FileSizeValidator convert the input so if you do
        both, you may convert a file size into kilo-bytes twice and get
        a number that is too big.
        """
        spec = []
        for argItem in self.orderedRequiredArgs:
            if (self.arguments[argItem]['takes_args']):
                spec.append(argItem + '=')
            else:
                spec.append(argItem)
        for argItem in self.orderedOptionalArgs:        
            self[argItem] = None
            if (self.arguments[argItem]['takes_args']):
                spec.append(argItem + '=')
            else:
                spec.append(argItem)

        args, opts = getopt(argv[2:],'',spec)
        if (opts != []):
            raise Exception, 'Received unexepcted arguments "' + `opts` + '".'
        
        for a in args:
            a = self.StripEq(a)
            argName = a[0][2:]
            argVal = a[1]
            if (None != argVal and '' != argVal.strip()):
                if (self.arguments[argName]['validator']):
                    argVal = self.arguments[argName]['validator'](argVal)
                self[argName] = argVal
            
        self.ComplainAboutMissingRequiredArguments()

    def ComplainAboutMissingRequiredArguments(self):
        for a in self.orderedRequiredArgs:
            a = self.StripEq(a)
            if (not self.argDict.has_key(a)):
                msg = ('Argument --' + a + ' missing for command '
                       + self.cmdName + '.')
                raise Exception, msg

    def WarnAboutLocalhostHostIfNecessary(self):

        if (None == self['host'] or '' == self['host'].strip()):
            self['host'] = dibs_options.hostname
        if (None == self['host'] or
            'localhost' == self['host'] or
            'localhost.localdomain' == self['host'] or
            '127.0.0.1' == self['host']):        
            print 'WARNING: host=' + `self['host']` + '; will probably fail.'

    def PrepareForDIBSCommand(self):
        """
        PrepareForDIBSCommand(self):

        This method should be called in the beginning of the run method
        of every command that uses the database.
        It locks the dibs_database, imports it and sets self.database
        to point to it.

        See Also: FinishDIBSCommand.
        """
        gotLock = self.TryToGetLock()

        import dibs_database

        self.database = dibs_database.DIBSDatabase()

        self.database.LoadFromFile(dibs_options.databaseFilePrefix)

    def FinishDIBSCommand(self):
        """
        FinishDIBSCommand(self):

        This method should be called at the end of every run method that
        calls PrepareForDIBSCommand.  This function saves the database
        and releases the lock obtained by PrepareForDIBSCommand.
        """
        self.database.SaveToFile(dibs_options.databaseFilePrefix)
        self.RemoveMyLock()
        del self.database

    def TryToGetLock(self):
        """
        Try to lock the database.  If we fail, sleep and try again.  If
        we fail after a bunch of tries, email the user and report the
        problem.
        """

        i = 0
        numTries = 20
        while(i < numTries):
            if (os.path.exists(dibs_options.lockfile)):
                print 'failed to get lock, sleeping...\n'
                time.sleep(9)
                i = i + 1
            else:
                fd = open(dibs_options.lockfile,'wU')
                fd.write('Locked on ' +
                         time.asctime(time.localtime(time.time())) +
                         ' by command ' + self.cmdName)
                fd.close()
                return 1
        msg = ('Could not aquire lock after ' + `numTries` + ' tries.\n' + 
              'If you determine that this is an error and no program has\n' + 
              'a valid lock, delete ' + dibs_options.lockfile + '.\n')
        raise Exception, msg

    def RemoveMyLock(self):
        RemoveLock()

def RemoveLock():
    if (os.path.exists(dibs_options.lockfile)):
        os.remove(dibs_options.lockfile)


def ConvertFileSizeToInteger(valueString):
    """
    ConvertFileSizeToInteger(valueString):
    
    This function converts a string represting a file size to an integer.
    The valueString can be an integer followed by one of the letters
    k, m, g, or t causing valueString to be multiplied by
    10^3, 10^6, 10^9, or 10^12.  If no letter is provided, then k is assumed.
    
    """
    L = len(valueString)
    lastChar = valueString[L-1]
    if (['0','1','2','3','4','5','6','7','8','9','l','L'].count(lastChar)):
        value = long(valueString)*1000 # no letter so assume it's in kilobytes
    else: # process letter size abbreviation
        value = long(valueString[0:(L-1)]) * 1000
        lastChar = lastChar.lower()
        if ('k' == lastChar):
            pass
        elif ('m' == lastChar):
            value *= 1000
        elif ('g' == lastChar):
            value *= 1000000
        elif ('t' == lastChar):
            value *= 1000000000
        else:
            msg = (valueString + ' must be integer ' +
                   ' or integer followed by {K,M,G,T} (e.g. 2M).')
            raise Exception, msg
    return value

class Validator:
    """
    A class to validate an argument type.  
    """
    def __init__(self):
        pass

    def Validate(self,arg):
        """
        Validate(self,arg):
        
        Make sure that arg has the valid type and raise an exception
        otherwise.  If succesful, return (the possibly modified) argument.
        """
        return arg

    def __call__(self,arg):
        return self.Validate(arg)

    def MakeMenuEntry(self,argFrame):
        """
        MakeMenuEntry(self,argFrame):

        argFrame:  A frame to create an entry for the argument in.

        This function will be called by the GUI to create the entry
        for the argument represented by a Validator instance.  This
        function should create an entry object that supports the
        get()/set(...) methods and create a menuEntry object that
        can be gridded into argFrame to allow the user to modify
        the given entry.

        The return value is (menuEntry, entry).
        """
        entry = Tkinter.StringVar()
        menuEntry = Tkinter.Entry(argFrame,textvariable=entry)
        return (menuEntry,entry)

class BooleanValidator(Validator):
    def __init__(self,default=0):
        Validator.__init__(self)
        self.default = default

    def Validate(self,arg):
        if (str == type(arg)):
            arg = arg.strip()
        if (None == arg or 0 == arg or '' == arg or '0' == arg):
            return 0
        else:
            return 1

    def MakeMenuEntry(self,argFrame):
        entry = Tkinter.StringVar()
        menuEntry = Tkinter.Checkbutton(argFrame,variable=entry)
        entry.set(self.default)
        return (menuEntry,entry)



class ChooseOneFromListValidator(Validator):
    """
    A class to validate choosing one type from a set.
    """
    def __init__(self,optionList,default):
        Validator.__init__(self)
        self.allowedTypes = list(optionList)
        self.default = default

    def Validate(self,arg):
        if (self.allowedTypes.count(arg)):
            return arg
        else:
            raise Exception, ('Invalid choice.  Must be one of ' +
                              `self.allowedTypes` + '.')

    def MakeMenuEntry(self,argFrame):
        entry = Tkinter.StringVar()
        menuEntry = apply(Tkinter.OptionMenu,[argFrame,entry] +
                          self.allowedTypes)
        entry.set(self.default)
        return (menuEntry,entry)

class TalkTypeValidator(ChooseOneFromListValidator):
    def __init__(self):
        ChooseOneFromListValidator.__init__(self,['active','passive','any'],
                                            'any')

class YesNoValidator(ChooseOneFromListValidator):
    def __init__(self,default):
        ChooseOneFromListValidator.__init__(self,['yes','no'],default)

class StrictTalkTypeValidator(ChooseOneFromListValidator):
    def __init__(self,default='active'):
        ChooseOneFromListValidator.__init__(self,['active','passive'],default)

class StringValidator(Validator):
    pass

class FileSizeValidator(Validator):
    def __init__(self):
        pass

    def Validate(self,arg):
        return ConvertFileSizeToInteger(arg)
        
class FloatValidator(Validator):
    def __init__(self,minVal=None,maxVal=None):
        self.minVal=minVal
        self.maxVal=maxVal

    def Validate(self,arg):
        value = float(arg)
        if (None != self.minVal and value < self.minVal):
            raise Exception, ('Value ' + `value` +
                              ' too small; minimum allowed value = ' +
                              `self.minVal` + '.')
        if (None != self.maxVal and value > self.maxVal):
            raise Exception, ('Value ' + `value` +
                              ' too big; maximum allowed value = ' +
                              `self.maxVal` + '.')
        return value

        
class IntegerValidator(Validator):
    def __init__(self,minVal=None,maxVal=None):
        self.minVal=minVal
        self.maxVal=maxVal

    def Validate(self,arg):
        value = long(arg)
        if (None != self.minVal and value < self.minVal):
            raise Exception, ('Value ' + `value` +
                              ' too small; minimum allowed value = ' +
                              `self.minVal` + '.')
        if (None != self.maxVal and value > self.maxVal):
            raise Exception, ('Value ' + `value` +
                              ' too big; maximum allowed value = ' +
                              `self.maxVal` + '.')
        return value

    
class ExistingFileNameValidator(Validator):
    def __init__(self,initialDir=None):
        Validator.__init__(self)
        if (None == initialDir):
            initialDir = os.getcwd()
        self.initialDir = initialDir

    def Validate(self,arg):
        if (None != arg and '' != arg.strip() and not os.path.exists(arg)):
            raise Exception, ('No file named ' + `arg` + ' exists.')
        else:
            return arg

    def MakeMenuEntry(self,argFrame):

        browseFrame = Tkinter.Frame(argFrame)
        entry = Tkinter.StringVar()
        menuEntry = Tkinter.Entry(browseFrame,textvariable=entry)
        browseButton = Tkinter.Button(
            browseFrame,text='(Browse)',command=
            lambda :BrowseForExistingFile(browseFrame,entry,self.initialDir))
        menuEntry.pack(side='top',expand=1,fill='x')
        browseButton.pack(side='top',expand=1,fill='x')

        return (browseFrame,entry)

def BrowseForExistingFile(parentWindow,stringVarToSet,initialDir):
    """
    BrowseForExistingFile(parentWindow,stringVarToSet):

    parentWindow:     Window to open dialog near.
    stringVarToSet:   A StringVar (or anything else with a set method) that
                      is set to the selected file.
    initialDir:       Directory to start dialog in.

    When this function is invoked, it creates a dialog box that the user
    can use to select an existing file.
    """
    stringVarToSet.set(parentWindow.tk.call(
        'tk_getOpenFile','-parent',parentWindow,'-initialdir',initialDir))
