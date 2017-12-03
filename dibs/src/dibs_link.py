

import os

if (os.name == 'nt' or os.name == 'dos'):
    try:
        from win32com.shell import shell
        import pythoncom
    except Exception, e:
        print 'WARNING: Received exception ' + `e` + ' in doing import.'
        print 'WARNING: Unable to import win32com.shell.shell, pythoncom.'
        print 'WARNING: Symbolic links and Shortcuts will not work.'
        def GetRealFilename( fileName ):
            return fileName
        def StripShortcutExtensionOnWindows( name ):
            raise 'Refusing to deal with shortcut file without win32com stuff.'

    from win32com.shell import shell
    import pythoncom, os

    class PyShortcut:
        def __init__( self ):
            self._base = pythoncom.CoCreateInstance(
                shell.CLSID_ShellLink, None,
                pythoncom.CLSCTX_INPROC_SERVER, shell.IID_IShellLink)
        def load( self, filename ):
            # Get an IPersist interface
            # which allows save/restore of object to/from files
            self._base.QueryInterface( pythoncom.IID_IPersistFile ).Load(
                filename )
        def save( self, filename ):
            self._base.QueryInterface( pythoncom.IID_IPersistFile ).Save(
                filename, 0 )
        def __getattr__( self, name ):
            if name != "_base":
                return getattr( self._base, name )

    def GetRealFilename( fileName ):
        L = len(fileName)
        if (fileName[(L-4):L] == '.lnk'):
            shortcut = PyShortcut()
            shortcut.load(fileName)
            return shortcut.GetPath(shell.SLGP_SHORTPATH)[0]
        else:
            return fileName
        
    def StripShortcutExtensionOnWindows( fileName ):
        L = len(fileName)
        if (fileName[(L-4):L] == '.lnk'):
            return fileName[0:(L-4)]
        else:
            return fileName

else:
    def GetRealFilename( fileName ):
        return os.path.realpath(fileName)

    def StripShortcutExtensionOnWindows( name ):
        return name
