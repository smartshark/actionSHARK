#!/bin/bash

current=`pwd`
mkdir -p /tmp/actionSHARK/
cp * /tmp/actionSHARK/
cp -R ../actionSHARK /tmp/actionSHARK/
cp ../setup.py /tmp/actionSHARK/
cp ../main.py /tmp/actionSHARK/
cp ../logger_config.json /tmp/actionSHARK/
cd /tmp/actionSHARK/


if [ -f "$current/actionSHARK_plugin.tar" ]; then
    rm "$current/actionSHARK_plugin.tar"
fi

tar -cvf "$current/actionSHARK_plugin.tar" --exclude=*.tar --exclude=build_plugin.sh --exclude=*/tests --exclude=*/__pycache__ --exclude=*.pyc *