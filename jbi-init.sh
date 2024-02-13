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
cd "${HOME}"
JBI_FOLDER=".jbi"
ARCHIVE_FOLDER="${HOME}/${JBI_FOLDER}-archive/$(date '+%Y-%m-%d_%H-%M-%S')"
# Check if the folder already exists, if so run some code
if [ -d "${JBI_FOLDER_PATH}" ]; then
    echo "JBI folder already exists."
    echo "Comitting changes to current repository at: ${pwd}"
    git pull origin main
    git add .
    git commit -m "default commit message"
    git push origin main

    # Create the archive directory
    mkdir -p "${ARCHIVE_FOLDER}"
    echo "Created archive folder: ${ARCHIVE_FOLDER}"

    # Now move the folder
    current_folder="${HOME}/${JBI_FOLDER}"
    archive_folder="${ARCHIVE_FOLDER}"
    echo -p "JBI_FOLDER exists about to move ${current_folder}} to ${archive_folder} right now!!!!"
    mv "${current_folder}" "${archive_folder}"

else
    echo "JBI folder does not exist."
    # Add your code here to run when the folder does not exist
fi

JBI_FOLDER_PATH="${HOME}/${JBI_FOLDER}"

git clone "https://github.com/MichaelOC23/setup.git"

# Use 'move' to rename the folder (. folders are hidden)
echo "about to mvoe setup to .jbi       "
echo "value of JBI_FOLDER__PATH is ${JBI_FOLDER_PATH}"
mv "${HOME}/setup" "${JBI_FOLDER_PATH}"

# Loop through each .sh file in the .jbi folder
for file in "${JBI_FOLDER_PATH}"/*.sh; do
    # Check if the file exists to avoid errors with non-existent files
    if [ -f "$file" ]; then
        # Make the file executable
        chmod u+x "$file"
        echo "Made executable: $file"
    fi
done

line_to_add='export PATH="$PATH:$HOME/.jbi/ENV_VARIABLES.sh"'
zshrc="${HOME}/.zshrc"

# Check if the line already exists in .zshrc
if ! grep -Fxq "${line_to_add}" "${zshrc}"; then
    # If the line does not exist, append it
    echo "${line_to_add}" >>"${zshrc}"
    echo "Line added to .zshrc"
else
    echo "Line already in .zshrc"
fi

source "${HOME}/.zshrc"
echo -e "\e[32mThe jbi-init.sh script has been run successfully.\e[0m"
