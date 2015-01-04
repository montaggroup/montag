Montag
======

If knowledge can create problems, it is not through ignorance that we can solve them.  
                                                                 ---      Isaac Asimov
                                                                        
                                                                        
Installation
============
see [here](docs/INSTALL_BANANAPI.md) for instructions for installation on a banana pi running ubuntu.  
Instructions for other systems running debian/ubuntu should not differ much.


Motivation
==========

Montag is intended to be a means to cheap and widely available education. In the 21th century
knowledge is the raw material without which success in life (however success may be defined in the readers culture)
becomed virtually impossible to attain.
Even though Article 13 of the United Nations' 1966 International Covenant on Economic, Social and Cultural Rights recognizes the right of everyone to an education economical, cultural and political circumstances often make it hard
for people to actually obtain one. Look up "student debt" for a short primer on why this is not just a 
third world problem.

The main idea behind Montag is to leverage the virtually nonexistent delivery cost for digital documents (think e-books,
tutorials, guides) to increase the availability of written information for as many human beings as possible.

The basic design is a massively replicated database of metadata about existing digital documents (called tomes) and 
their authors as well as related files holding content. Transmission of database entries is done in a web of trust
fashion, so by design everybody can add and edit entries. Synchronization of data is done in full by default, so every
node hold the full repositry of the entire web of trust's data. This may appear wasteful in terms of bandwidth and
storage space but is a core design paradigm for several reasons, the most important of which are:
* Access to the data is always node-local, so people do not see which documents a user reads. Who reads a book about AIDS, an "evil" foreign religion or "comunist" economic models if you know your family / employer / neighbor / government might be looking over your shoulder?
* The data becomes massively redundant, making it hard to erase it. Montag is named after Guy Montag for a reason. Who is Guy Montag? Look him up and read a good book!
* The local storage also makes it useful during internet outages when you actually have time to read a good book.
* Complete offline synchronization is possible for people without decent internet connections. Care package FTW!



