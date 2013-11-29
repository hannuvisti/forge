#!/bin/sh

APPDIR=/usr/local/forge
MOUNTDIR=/mnt/image
USERNAME=visti


# Do not modify these below
CHELPERDIR=$APPDIR/chelper
CHELPER=$CHELPERDIR/chelper
REPOSITORY=$APPDIR/repository
TRIVIALREP=$REPOSITORY/repository
SECRETREP=$REPOSITORY/secretrepository
DATABASE=$APPDIR/forensic/sqlite.db
CREATORDIR=$APPDIR/creator
IMAGEDIR=$APPDIR/Images

# Mandatory requirements
if [ `id -u` -ne 0 ]; then
    echo "must be run as root"
    exit 1
fi

if [ -d "$APPDIR" ]; then
    echo "application directory exists, no modifications done"
    exit 1
fi

# Create directories
echo "create directories"
mkdir -p $APPDIR 
if [ $? -ne 0 ]; then
    echo "cannot create $APPDIR"
    exit 1
fi
mkdir -p $CHELPERDIR
if [ $? -ne 0 ]; then
    echo "cannot create $CHELPERDIR"
    exit 1
fi
mkdir -p $SECRETREP 
if [ $? -ne 0 ]; then
    echo "cannot create $SECRETREP"
    exit 1
fi
mkdir -p $TRIVIALREP
if [ $? -ne 0 ]; then
    echo "cannot create $TRIVIALREP"
    exit 1
fi
mkdir -p $IMAGEDIR
if [ $? -ne 0 ]; then
    echo "cannot create $IMAGEDIR"
    exit 1
fi

# Copy directories
echo "copy items"
cp -r ./forensic $APPDIR
cp -r ./creator $APPDIR
cp -r ./chelper $APPDIR

#process files
echo "process wsgi.py"
cat $APPDIR/forensic/forensic/wsgi.py_ | sed s#@@CREATORDIR@@#$CREATORDIR# > $APPDIR/forensic/forensic/wsgi.py
rm $APPDIR/forensic/forensic/wsgi.py_

echo "process settings.py"
cat $APPDIR/forensic/forensic/settings.py_ | sed s#@@DATABASE@@#$DATABASE# | sed s#@@REPOSITORY@@#$REPOSITORY# > $APPDIR/forensic/forensic/settings.py
rm $APPDIR/forensic/forensic/settings.py_

echo "process uitools.py"
cat $APPDIR/forensic/ui/uitools.py_ | sed s#@@CHELPER@@#$CHELPER# > $APPDIR/forensic/ui/uitools.py
rm $APPDIR/forensic/ui/uitools.py_

echo "process models.py"
cat $APPDIR/forensic/ui/models.py_ | sed s#@@IMAGEDIR@@#$IMAGEDIR# | sed s#@@MOUNTPOINT@@#$MOUNTDIR# > $APPDIR/forensic/ui/models.py
rm $APPDIR/forensic/ui/models.py_

echo "process ntfsc.py"
cat $APPDIR/creator/ntfsparser/ntfsc.py_ | sed s#@@CHELPER@@#$CHELPER# > $APPDIR/creator/ntfsparser/ntfsc.py 
rm $APPDIR/creator/ntfsparser/ntfsc.py_

echo "process fat.py"
cat $APPDIR/creator/fat/fat.py_ | sed s#@@CHELPER@@#$CHELPER# > $APPDIR/creator/fat/fat.py
rm $APPDIR/creator/fat/fat.py_


echo "creating chelper"
cat $CHELPERDIR/chelper.h_ | sed s#@@IMAGEDIR@@#$IMAGEDIR# | sed s#@@MOUNTPOINT@@#$MOUNTDIR# > $CHELPERDIR/chelper.h
cd $CHELPERDIR
make && chmod 4711 chelper
rm Makefile
rm chelper.h
rm chelper.c
rm chelper.h_

cd $APPDIR
chown -R $USERNAME creator forensic Images repository


echo "all done. Now exit root, change to $APPDIR/forensic"
echo "and run python manage.py syncdb"
echo "Finally start Django"
echo "python manage.py runserver"






