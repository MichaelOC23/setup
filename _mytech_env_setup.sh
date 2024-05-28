# !/bin/bash

# note change the above to #!/bin/bash if you are using bash .... NOT SURE what server will be running
clear
# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

CURRENT_DIR=$(basename "$PWD")

echo "Script directory: $SCRIPT_DIR"

# Change to that directory
cd "$SCRIPT_DIR" || exit 1

# Get the path of the requirements file
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
echo "Requirements file: $REQUIREMENTS_FILE"

VENV_NAME="jbi_venv"

# add a symbolic link to the another folder with py files (if it doesn't exist)
[ -d classes ] || ln -s ${HOME}/code/mytech/classes ./classes

# Form the name of the virtual environment directory
VENV_DIR="${SCRIPT_DIR}/$VENV_NAME"
echo "Virtual environment directory: $VENV_DIR"

# Full path to the virtual environment directory
FULL_VENV_PATH="${SCRIPT_DIR}/${VENV_NAME}"
echo "Full path to virtual environment directory: $FULL_VENV_PATH"

# Delete the directory
rm -rf "$FULL_VENV_PATH"

# Create a new virtual environment
python3 -m venv "/$FULL_VENV_PATH" || {
    echo "Creating virtual environment at $FULL_VENV_PATH failed"
    exit 1
}

# Change directory
cd $FULL_VENV_PATH || {
    echo "Changing directory failed"
    exit 1
}

# Activate the virtual environment
source "$FULL_VENV_PATH/bin/activate" || {
    echo "Activating virtual environment failed"
    exit 1
}

# Upgrade pip
pip install --upgrade pip || {
    echo "Pip upgrade failed"
    exit 1
}

# Continue with the rest of the script if the user answered "yes"
echo "Proceeding with the installation of all libraries ..."
# Install requirements
pip install -r $REQUIREMENTS_FILE || {
    echo "Requirements installation failed"
    exit 1
}
# ### Change to that directory
cd "$SCRIPT_DIR" || exit 1
# ### Backup current requirements
mkdir -p .req_backup
cp $REQUIREMENTS_FILE ".req_backup/requirements_raw_$(date +%Y%m%d_%H%M%S).txt"

# ### Freeze the current state of packages
pip freeze >".req_backup/requirements_freeze_$(date +%Y%m%d_%H%M%S).txt"

echo -e "\033[5;34m *** INSTALLATION COMPLETE *** \033[0m"
