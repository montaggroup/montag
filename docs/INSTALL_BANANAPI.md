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



        sudo apt-get update
        sudo apt-get install git python-pip python-virtualenv
        sudo apt-get install libxml2-dev libxslt-dev libz-dev python-dev
        git clone https://github.com/montaggroup/montag.git
        cd montag
        virtualenv venv
        source venv/bin/activate
        pip install -r requirements.txt
        ./montag-services.py start
        
Remark: the 'pip install' command can take 30 minutes to complete, this is normal.
Now start your browser and surf to http://localhost:8000 (or http://\[ip of Banana Pi\]:8000 if not an the same machine).        
        
Whenever you want to start Montag fresh (i.e. after a reboot) use:

        cd montag
        source venv/bin/activate
        ./montag-services.py start

If you want to, create a separate user for Montag (i.e. "montag").