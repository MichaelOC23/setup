#!/bin/bash 
#Install Command
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichaelOC23/setup/main/jbi-init.sh)"

#Custom hidden root folder for JBI machines to install software
cd ~
JBI_FOLDER = ".jbi"

echo $JBI_FOLDER
mkdir -p $JBI_FOLDER

JBI_FOLDER_PATH="$HOME/$JBI_FOLDER"

echo $JBI_FOLDER_PATH

setup_file_name="jbi-setup.sh"
env_file_name="env_variables.sh"

setup_file_path = "$JBI_FOLDER_PATH/$setup_file_name"
env_file_path = "$JBI_FOLDER_PATH/$env_file_name"

echo $setup_file_path
echo $env_file_path

setup_url="https://raw.githubusercontent.com/MichaelOC23/setup/main/jbi-setup.sh"
env_url="https://raw.githubusercontent.com/MichaelOC23/setup/main/env_variables.sh"

# Use curl to download the file
curl -L $setup_url -o $setup_file_path
curl -L $env_url -o $env_file_path

# Or make it executable and then run it
chmod +x $JBI_FOLDER_PATH/$setup_file_name
chmod +x $JBI_FOLDER_PATH/$env_file_name

echo "export PATH=\"\$PATH:\$HOME/.jbi/env_variables.sh"\" >> ~/.zshrc
source "$HOME/.zshrc"

$JBI_FOLDER_PATH/$setup_file_name


