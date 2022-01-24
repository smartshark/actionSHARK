#!/bin/sh
PLUGIN_PATH=$1
cd $PLUGIN_PATH

# Install actionSHARK
python $PLUGIN_PATH/setup.py install --user