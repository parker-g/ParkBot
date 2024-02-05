#!/usr/bin/env sh
# provides a setup which can be used from an ssh context without x-11 forwarding

# Function to compare Python versions
version_gt() {
    test "$(printf '%s\n' "$@" | sort -V | head -n 1)" != "$1"
}
python_version=$(python --version 2>&1)
if [ $? -eq 0 ]; then
    # Extract and compare Python version
    python_version_number=$(python -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
    if version_gt "$python_version_number" "3.10"; then
        python_keyword="python"
    else
        echo "Keyword 'python' version is not higher than 3.10."
    fi
fi
python3_version=$(python3 --version 2>&1)
if [ $? -eq 0 ]; then
    # Extract and compare Python version
    python3_version_number=$(python3 -c "import sys; print('.'.join(map(str, sys.version_info[:3])))")
    if version_gt "$python3_version_number" "3.10"; then
        python_keyword="python3"
    else
        echo "Keyword 'python3' version is not higher than 3.10."
    fi
fi
# If neither 'python' nor 'python3' is available or version is not higher than 3.10
if [ -z "$python_keyword" ]; then
    echo "Neither 'python' nor 'python3' is available or the version is not higher than 3.10."
else
    echo "Using Python keyword: $python_keyword"
fi
# now we have acquired a working python keyword, and confirmed it's above version 3.10, in the variable $python_keyword

"$python_keyword" config/venv-setup.py # creates venv, installs pip dependencies
activate_script=$(find .venv -name activate)
source "${activate_script}"
"$python_keyword" config/external-dep-setup.py # installs external dependencies (lavalink, nssm for windows, java) and installs lavalink + parkbot as services