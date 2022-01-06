#!/bin/bash

current=`pwd`
mkdir -p /tmp/actionSHARK/
cp -R ../actionshark /tmp/actionSHARK/
cp ../setup.py /tmp/actionSHARK/
cp ../main.py /tmp/actionSHARK
cp ../loggerConfiguration.json /tmp/actionSHARK
cp * /tmp/actionSHARK/
cd /tmp/actionSHARK/

tar -cvf "$current/actionSHARK_plugin.tar" --exclude=*.tar --exclude=build_plugin.sh --exclude=*/tests --exclude=*/__pycache__ --exclude=*.pyc *