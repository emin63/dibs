

import os, os.path, glob

from distutils.core import setup

def MakeDocs():
    try:
        p = os.popen('cd doc; make all 2>&1','r')
        output = p.read()
        status = p.close()
        if (status):
            msg = ('Could not create documentation.  Received output \n' +
                   '-'*70 + '\n' + output + '-'*70 +
                   '\nand status ' + `status` + '\nUsing pre-built docs.\n')
            print 'WARNING: ' + msg
            for file in map(lambda x: os.path.join('doc',x),docFiles):
                fd = open(file,'w')
                fd.write('ERROR: Could not create this file during install.\n')
                fd.close()
    except Exception, e:
        print ('WARNING: Could not create documentation because of exception '
               + `e` + '.\nUsing pre-built docs.\n')
        

def GetFilesWithExtensionsFromDir(dir,extenstionList):
    result = []
    for file in os.listdir(dir):
        for ext in extenstionList:
            fileNameLen = len(file)
            extNameLen = len(ext)
            if (file[(fileNameLen-extNameLen):] == ext):
                result.append(os.path.join(dir,file))
    return result


docFiles = map(lambda x: os.path.join('doc',x),
               ['dibs-faq.html','dibs.html','dibs.info'])

basicProductInfoFiles = ['LICENSE','CHANGELOG','README','RELEASE_NOTES']

dataFiles = [(os.path.join('doc','dibs'),docFiles+basicProductInfoFiles),
             (os.path.join('share','dibs','cgi-bin'),
              GetFilesWithExtensionsFromDir('src/peer_finder/cgi-bin',
                                            ['.py','.cgi','README']))]

MakeDocs()


setup(name="DIBS",
      version="0.93",
      description="Distributed Internet Backup System",
      author="Emin Martinian",
      author_email="emin@alum.mit.edu",
      url="http://dibs.sourceforge.net",
      packages=['dibs_lib','dibs_lib.ffield','dibs_lib.peer_finder',
                'dibs_lib.dibs_commands'],
      package_dir = {'dibs_lib':'src'},
      scripts=['src/dibs.py'],
      data_files=dataFiles)



