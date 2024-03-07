#!/bin/sh
# curl
python3 -m venv .
source bin/activate
cd MTECmqtt
python3 setup.py install
cd ..
