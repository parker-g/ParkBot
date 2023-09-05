#!/usr/bin/env sh
# test script

# 1. create python virtual environment 
WORKING_DIRECTORY=$(pwd)
PYTHON="$(WORKING_DIRECTORY)/.venv/Scripts/python"
"$PYTHON -m venv .venv"
source "$(WORKING_DIRECTORY)/.venv/Scripts/activate"
"$(PYTHON) -m pip install -r requirements.txt"
# virtual environment activated

# 2. check if 7zip is installed, if not then download it

# 3. check if FFMPEG is downloaded, if not then download FFMPEG and store it's executable as an env variable.

# 



# run config wizard