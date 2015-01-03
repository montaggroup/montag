Install Montag on a Banana Pi
=============================

Montag is a lot of fun on small embedded Linux boards, _but_ it is painfully slow on a Raspberry Pi. With two CPU cores
and 1 GB of RAM, the Banana Pi is a reasonable choice for the task.
 
The main amount of storage space will be needed for the ''Filestore'', which may not fit on the SD card which holds
the operating system. On a Banana Pi you can connect a 2,5" HDD (either through USB or SATA) or even SSD (preferably
through SATA). Alternatively, if a NAS or other file server is available in the LAN the ''Filestore'' can be put there.

We start with the necessary hardware:
*   one [Banana Pi](http://www.bananapi.org/p/product.html) with a decent power supply
*   one decent SD card (e.g. SanDisk, Kingston), it absolutely needs to support wear levelling




sudo apt-get install git python-pip python-virtualenv
git clone https://github.com/montaggroup/montag.git



If you want to, create a separate user for Montag (i.e. "montag").