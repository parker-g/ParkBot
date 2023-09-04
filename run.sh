#!/usr/bin/env sh
# test script

# create python virtual environment 

WORKING_DIRECTORY=$(pwd)
PYTHON="$(WORKING_DIRECTORY)/.venv/Scripts/python"
"$PYTHON -m venv .venv"
source "$(WORKING_DIRECTORY)/.venv/Scripts/activate"
"$(PYTHON) -m pip install -r requirements.txt"
# virtual environment activated

# download FFMPEG and store it's executable as an env variable.


# run config wizard