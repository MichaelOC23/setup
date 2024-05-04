#!/bin/bash

#Clear the terminal
clear

#make the llm_launch.sh file executable if it exists in the current directory
[ -f llm_launch.sh ] && chmod u+x llm_launch.sh

# Get the directory where the script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)" # get the directory where the script is located ... full path
CURRENT_DIR=$(basename "$PWD")                             #should be communify, the name of the project

echo -e "Script directory: ${SCRIPT_DIR}\033[0m"
echo -e "Current directory: ${CURRENT_DIR}\033[0m"

# Change to that directory
cd "${SCRIPT_DIR}" || exit 1

# Get the path of the requirements file
REQUIREMENTS_FILE="${SCRIPT_DIR}/requirements.txt"
echo -e "Requirements file: ${REQUIREMENTS_FILE}\033[0m"

# Name of the virtual environment
VENV_NAME="${CURRENT_DIR}_venv"

# Form the name of the virtual environment directory
VENV_DIR="${SCRIPT_DIR}/${VENV_NAME}"
echo -e "Virtual environment directory: ${VENV_DIR}\033[0m"

# add a symbolic link to the another folder with py files (if it doesn't exist)
[ -d classes ] || ln -s ${HOME}/.jbi/classes ./classes

# Full path to the virtual environment directory
FULL_VENV_PATH="${SCRIPT_DIR}/${VENV_NAME}"
echo -e "Full path to virtual environment directory: ${FULL_VENV_PATH}\033[0m"

# Delete the directory
rm -rf "${FULL_VENV_PATH}"

# Create a new virtual environment
python3 -m venv "/${FULL_VENV_PATH}" || {
    echo -e "\033[1;31mCreating virtual environment at ${FULL_VENV_PATH} failed\033[0m"
    exit 1
}
echo -e "\033[1;32mVirtual environment created successfully\033[0m"

# Change directory
cd ${FULL_VENV_PATH} || {
    echo -e "\033[1;31mChanging directory failed\033[0m"
    exit 1
}
echo -e "\033[1;32mChanged directory successfully\033[0m"

# Activate the virtual environment
source "${FULL_VENV_PATH}/bin/activate" || {
    echo -e "\033[1;31mActivating virtual environment failed\033[0m"
    exit 1
}
echo -e "\033[1;32mActivated virtual environment successfully\033[0m"

# Upgrade pip
pip install --upgrade pip || {
    echo -e "\033[1;31mPip upgrade failed\033[0m"
    exit 1
}
echo -e "\033[1;32mPip upgrade successful\033[0m"

# Install requirements
echo -e "\n\n\033[4;32mProceeding with the installation of all libraries ...\033[0m"
pip install -r ${REQUIREMENTS_FILE} || {
    echo -e "\033[1;31mRequirements installation failed\033[0m"
    exit 1
}
#install azure swagger client
# pip install ./classes/azure_S2T_swagger_client

echo -e "\033[1;32mRequirements installation successful\033[0m"

# ### Change to that directory
cd "${SCRIPT_DIR}" || exit 1
# ### Backup current requirements
mkdir -p .req_backup
cp ${REQUIREMENTS_FILE} ".req_backup/requirements_raw_$(date +%Y%m%d_%H%M%S).txt" || {
    echo -e "\033[1;31mRequirements backup failed\033[0m"
    exit 1
}
echo -e "\033[1;32mRequirements backup successful\033[0m"

# ### Freeze the current state of packages
pip freeze >".req_backup/requirements_freeze_$(date +%Y%m%d_%H%M%S).txt" || {
    echo -e "\033[1;31mFreezing requirements failed\033[0m"
    exit 1
}
echo -e "\033[1;32mFreezing requirements successful\033[0m"

echo -e "\033[5;32mInstallation complete\033[0m"
