#!/bin/bash 
#Install Command
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichaelOC23/setup/main/jbi-init.sh)"

#Custom hidden root folder for JBI machines to install software
cd ~
JBI_FOLDER = ".jbi"

JBI_FOLDER_PATH="$HOME/$JBI_FOLDER"

setup_file_name="jbi-setup.sh"
env_file_name="env_variables.sh"

ssetup_url="https://raw.githubusercontent.com/MichaelOC23/setup/main/jbi-setup.sh"
setup_url="https://raw.githubusercontent.com/MichaelOC23/setup/main/env_variables.sh"

# Use curl to download the file
curl -L $url -o "$JBI_FOLDER_PATH/$setup_file_name"
curl -L $url -o "$JBI_FOLDER_PATH/$env_file_name"

# Or make it executable and then run it
chmod +x $JBI_FOLDER_PATH/$setup_file_name
chmod +x $JBI_FOLDER_PATH/$env_file_name

echo "export PATH=\"\$PATH:\$HOME/.jbi/env_variables.sh"\" >> ~/.zshrc
source "$HOME/.zshrc"

$JBI_FOLDER_PATH/$setup_file_name


