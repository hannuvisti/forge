#!/bin/bash

# An example script to create a simple web history
# Sleeps are needed to get background processes up and running
# You can access the results on the host computer at 
# /var/lib/lxc/forge-lxc/rootfs/home/forge/.cache/.....


CHELPER=/usr/local/forge/chelper/chelper


$CHELPER lxc lxc-destroy
$CHELPER lxc lxc-create
sleep 5
$CHELPER lxc lxc-attach wait apt-get install -y xvfb
$CHELPER lxc lxc-attach wait apt-get install -y firefox


$CHELPER lxc lxc-attach nowait Xvfb :1 -screen 0 1024x768x24
sleep 1
$CHELPER lxc lxc-attach nowait su - forge -c "firefox --display=:1 http://news.bbc.co.uk"
sleep 1

$CHELPER lxc lxc-attach wait su - forge -c "firefox --display=:1 http://www.westminster.ac.uk"
$CHELPER lxc lxc-attach wait su - forge -c "firefox --display=:1 http://www.hannuvisti.com"
$CHELPER lxc lxc-attach wait su - forge -c "firefox --display=:1 http://www.cnn.com"
$CHELPER lxc lxc-attach wait su - forge -c "firefox --display=:1 http://www.finnair.com"

$CHELPER lxc lxc-stop
$CHELPER lxc lxc-start


