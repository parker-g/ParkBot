#!/usr/bin/env sh
# on linux, run this script with root permissions: `sudo bash setup.sh`

bash setup-no-gui.sh
"$python_keyword" config/config-wiz.py # takes user inputs for config fields, and writes them to the config file. 