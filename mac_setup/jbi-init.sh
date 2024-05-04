#!/bin/bash
#Install Command
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichaelOC23/setup/main/jbi-init.sh)"

clear

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if Homebrew is installed
check_homebrew_installed() {
    if brew --version &>/dev/null; then
        echo "Homebrew is already installed."
        return 0
    else
        echo "Homebrew is not installed."
        return 1
    fi
}
# Function to install Homebrew
install_homebrew() {
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to your PATH in /Users/yourname/.zprofile:
    eval "$(/opt/homebrew/bin/brew shellenv)"
}
# Function to check if Git is installed
check_git_installed() {
    if git --version &>/dev/null; then
        echo "Git is already installed."
        return 0
    else
        echo "Git is not installed."
        return 1
    fi
}
# Function to install Git
install_git() {
    echo "Installing Git..."
    brew install git
    echo "Installing github"
    brew install gh
}

# Check if Homebrew is installed, if not, install it
if ! check_homebrew_installed; then
    install_homebrew
    if ! check_homebrew_installed; then
        echo "Failed to install Homebrew. Cannot proceed with Git installation."
        exit 1
    fi
fi

# Check if Git is installed, if not, install it
if ! check_git_installed; then
    install_git
fi

# Confirm the installation
if check_git_installed; then
    echo "Git installation was successful."
else
    echo "Git installation failed."
    exit 1
fi

#Archvie the current .jbi folder if there is one

#Custom hidden root folder for JBI machines to install software
HOME_DIR="${HOME}"
cd "${HOME}"
echo "Current directory is ${PWD} after cd to ${HOME_DIR}"

JBI_FOLDER=".jbi"
JBI_FOLDER_PATH="${HOME}/${JBI_FOLDER}"
ARCHIVE_FOLDER_DATE_NAME="$(date '+%Y-%m-%d_%H-%M-%S')"
ARCHIVE_FOLDER_DATE_PATH="${HOME}/.jbi-archive/${ARCHIVE_FOLDER_DATE_NAME}"
echo "ARCHIVE_FOLDER_DATE_NAME is ${ARCHIVE_FOLDER_DATE_NAME}"
echo "JBI_FOLDER is ${JBI_FOLDER} and ARCHIVE_FOLDER_DATE_NAME is ${ARCHIVE_FOLDER_DATE_NAME} and JBI_FOLDER_PATH is ${JBI_FOLDER_PATH}"

# Check if the folder already exists, if so run some code
if [ -d "${JBI_FOLDER_PATH}" ]; then
    echo "JBI folder already exists."

    # Create the archive directory
    mkdir -p .jbi-archive
    cd .jbi-archive
    mkdir -p $ARCHIVE_FOLDER_DATE_NAME

    cd "${HOME}"

    # Now move the folder
    echo "Since the JBI_FOLDER exists we are going to move ${JBI_FOLDER_PATH} to ${ARCHIVE_FOLDER_DATE_PATH}"
    mv "${JBI_FOLDER_PATH}" "${ARCHIVE_FOLDER_DATE_PATH}"

else
    echo "JBI folder does not exist."
    # Add your code here to run when the folder does not exist
fi

git clone https://github.com/MichaelOC23/setup.git "${JBI_FOLDER_PATH}"

# Use 'move' to rename the folder (. folders are hidden)
# echo -p "about to mvoe setup to .jbi       "
# mv "${HOME}/setup" "${JBI_FOLDER_PATH}"

# Loop through each .sh file in the .jbi folder
for file in "${JBI_FOLDER_PATH}"/*.sh; do
    # Check if the file exists to avoid errors with non-existent files
    if [ -f "$file" ]; then
        # Make the file executable
        chmod u+x "$file"
        echo "Made executable: $file"
    fi
done

# Define the line to add
line_to_add='source "${HOME}/.jbi/env_variables.sh"'

# Define the path to your .zshrc
zshrc="$HOME/.zshrc"

# Check if the line already exists in .zshrc
if ! grep -Fxq "$line_to_add" "$zshrc"; then
    # If the line does not exist, append it
    echo "$line_to_add" >>"$zshrc"
    echo "Line added to .zshrc"
else
    echo "Line already in .zshrc"
fi

source "${HOME}/.zshrc"
echo "The jbi-init.sh script has been run successfully."
