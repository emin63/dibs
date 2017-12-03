
* Foreward (Please Read)

The Distributed Internet Backup System (DIBS) was developed many years ago.
It was an interesting idea, but was overtaken by the early cloud storage
providers such as Mozy, Carbonite, Dropbox, and others.

Because the old MIT web page for DIBS is being shutdown and there seems
to be some interest in blockchain based cloud storage, a new github
repo was created to house DIBS at https://github.com/emin63/dibs.

Probably some work needs to be done on DIBS to make it useful. A good
place to start might be to put together a simple docker based test as
started in dibs/scripts/docktest.

* OVERVIEW

This file is a brief description of the Distributed Internet
Backup System (DIBS) package.  

Since disk drives are cheap, backup should be cheap too.  Of course it
does not help to mirror your data by adding more disks to your own
computer because a virus, fire, flood, robbery, power surge,
etc. could still wipe out your local data center.  Instead, you should
give your files to peers (and in return store their files) so that if
a catastrophe strikes your area, you can recover data from surviving
peers.  The Distributed Internet Backup System (DIBS) is designed to
implement this vision.

Note that DIBS is a backup system not a file sharing system like
Napster, Gnutella, Kazaa, etc.  In fact, DIBS encrypts all data
transmissions so that the peers you trade files with can not access
your data.

* DOCUMENTATION

The DIBS distribution contains extensive documentation in the doc
directory.  See doc/dibs.{info,html,dvi} for documentaion.  In
particular the Installation section of the manual describes how to
install everything and get started.  See doc/dibs-faq.html for a list
of frequently asked questions including the many ways in which DIBS
may be useful to you.

* OBTAINING

To obtain DIBS go to

  * http://dibs.sourceforge.net
  * http://www.csua.berkeley.edu/~emin/source_code/dibs
  * freshmeat.net. 

* USING

For detailed instructions, read the accompnaying documentation.  If
you just want to get started immediately, you can start the graphical
user interface by typing "dibs.py" at the command line (without the
quotes) after you install DIBS.


* FEEDBACK

Please contact emin@alum.mit.edu with questions and comments.

