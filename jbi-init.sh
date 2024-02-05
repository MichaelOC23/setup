#!/bin/bash 
#Install Command
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichaelOC23/setup/main/jbi-init.sh)"

#Custom hidden root folder for JBI machines to install software
cd ~
echo "This will install: Homebrew and Microsoft 365/Azure Authenticaiton"
    
if ! command -v brew &>/dev/null; then
  echo "Homebrew is not installed. Installing Homebrew..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> "$HOME/.zprofile"
  eval "$(/opt/homebrew/bin/brew shellenv)"
else
  echo "Homebrew is already installed."
fi


if ! command -v az &>/dev/null; then
  echo "Azure CLI is not installed. Attempting to install..."
  brew install azure-cli
else
  echo "Azure CLI is already installed. Attempting to upgrade..."
  brew upgrade azure-cli
fi
az login
az extension add --name azure-devops
az devops configure --defaults organization=https://dev.azure.com/justbuildit


if brew list --versions git >/dev/null; then
  echo "Git is already installed through Homebrew. Attempting to upgrade..."
  brew upgrade git
else
  echo "Git is not installed through Homebrew. Attempting to install..."
  brew install git
fi

#clone the mac setup folder
echo "$HOME is Home"
rm -rf "$HOME/.jbi"
git clone https://justbuildit@dev.azure.com/justbuildit/product/_git/macsetup "$HOME/.jbi/"


# Use curl to download the file
# curl -L $url -o "$JBI_FOLDER_PATH/$setup_file_name"
# curl -L $url -o "$JBI_FOLDER_PATH/$env_file_name"

# Or make it executable and then run it
chmod u+x ~/.jbi/ENV_VARIABLES.sh
chmod u+x ~/.jbi/jbi_init.sh
chmod u+x ~/.jbi/jbi_setup.sh

echo "export PATH=\"\$PATH:\$HOME/.jbi/ENV_VARIABLES.sh"\" >> ~/.zshrc

source "$HOME/.zshrc"
