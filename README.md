# ForGE

Forensic test image generator v1.1
Copyright Hannu Visti 2013, licenced under Gnu General Public Licence

## Overview

ForGe is a tool designed to build computer forensic test images. It was done as a MSc project for 
the University of Westminster. Its main features include:

* Web browser user interface
* Rapid batch image creation (only NTFS supported)
* Possibility to define a scenario including trivial and hidden items on images
* Variance between images. For example, if ForGe was told to put 10-20 picture files to a directory /holiday and
  create 10 images, all these images would have random pictures pulled from repository.
* Variance in timestamps. Each trivial and hidden file can be timestamped to a specific time. Each scenario is
  given a time variance parameter in weeks. If this is set to 0, every image receives an identical timeline. If
  nonzero, a random amount of weeks up to the maximum set is added to each file on each image
* Can modify timestamps to simulate certain disk actions (move, copy, rename, delete)
* Implements several data hiding methods: Alternate data streams, extension change, file deletion, concatenation
  of files and file slack space. 
* New data hiding methods can be easily implemented. Adding a new file system is also documented.


## Components and requirements
The application is built in Python and a helper application "chelper" in C. ForGe is guaranteed to work in the following environment but slight version deviations are not expected to cause problems. ForGe is written in Python 2.7 and does not support Python 3 syntax.

* Ubuntu 64 bit 12.04
* Django 1.5.1
* Python 2.7.3 - 2.7.5
* Tuxera NTFS-3G 2013.1.13 (the default in Ubuntu 12.04 is an older version, which does weird things to attributes of deleted files)

Other Linux versions than Ubuntu are likely to work. The key element is the existence of loopback devices /dev/loopX, as they are used to mount images in process.

## Installation instructions
See file Doc/Installation.txt. An installer script exists to do most of the work with minor configuration. 

## Stuff
The tool was and still is an academic project to be used by forensic experts. It does not even try tro prevent user errors and recover from deliberate misuse. 

NTFS parser component can be of interest to other file system related projects. It parses the most complex NTFS attributes (directory structures) and allows a framework to extend upon. 

## Documentation
A simple manual and extension design notes can be found in Documentation. 


### Author and contact details
Hannu Visti
<br>
hannu.visti@gmail.com

Comment, suggestions and feedback are welcome. 
