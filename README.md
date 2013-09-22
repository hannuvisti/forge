
ForGe
Forensic test image generator
Copyright Hannu Visti 2013, licenced under Gnu General Public Licence

1. Purpose of the application
ForGe is a tool designed to build computer forensic test images. It was done as a MSc project for 
the University of Westminster. Its main features include
- Web browser user interface
- Rapid batch image creation (only NTFS supported)
- Possibility to define a scenario including trivial and hidden items on images
- Variance between images. For example, if ForGe was told to put 10-20 picture files to a directory /holiday and
  create 10 images, all these images would have random pictures pulled from repository.
- Variance in timestamps. Each trivial and hidden file can be timestamped to a specific time. Each scenario is
  given a time variance parameter in weeks. If this is set to 0, every image receives an identical timeline. If
  nonzero, a random amount of weeks up to the maximum set is added to each file on each image
- Can modify timestamps to simulate certain disk actions (move, copy, rename, delete)
- Implements several data hiding methods: Alternate data streams, extension change, file deletion, concatenation
  of files and file slack space. 
- New data hiding methods can be easily implemented. Adding a new file system is also documented.

2. Components and requirements
The application is built in Python. A helper application "chelper" in C. The user interface is built around Django.
It works in the following environment:
Ubuntu 64 bit 12.04
Django 1.5.1
Python 2.7.3-2.7.5
Tuxera NTFS-3G 2013.1.13  (the default in Ubuntu 12.04 is an older version, which does weird things to attributes
       	       		   of deleted files)
Other Linux versions are likely to work as well but they have not been tested.

3. Installation instructions
See file INSTALLATION

4. Stuff
The tool was and still is an academic project. It is not designed to be a ready product but a prototype. The 
NTFS parser component can be of interest to other file system related projects. 

5. Documentation
A simple manual and extension design notes can be found in Documentation


Hannu Visti
London 20/9/2013
hannu.visti@gmail.com



