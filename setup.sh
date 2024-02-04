#!/usr/bin/env sh

python config/venv-setup.py # creates venv, installs pip dependencies
source .venv/Scripts/activate
python config/external-dep-setup.py # determines OS, checks for installation of FFMPEG, downloads FFMPEG. downloads NSSM and installs ParkBot as a Windows service if OS is Windows
if [$(uname) == "Linux"]; then
    python config/linux-service-manager.py
fi 
python config/config-wiz.py # takes user inputs for config fields, and writes them to the config file. 