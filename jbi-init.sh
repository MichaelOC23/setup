#!bin/bash 
#Install Command
# /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/MichaelOC23/setup/main/jbi-init.sh)"

#Custom hidden root folder for JBI machines to install software

JBI_FOLDER = "$HOME/.jbi"
mkdir -p $JBI_FOLDER

setup_file_name="jbi-setup.sh"
env_file_name="env_variables.sh"

setup_url="https://github.com/MichaelOC23/setup/tree/main/jbi-setup.sh"
setup_url="https://github.com/MichaelOC23/setup/tree/main/env_variables.sh"

# Use curl to download the file
curl -L $url -o "$JBI_FOLDER/$setup_file_name"
curl -L $url -o "$JBI_FOLDER/$env_file_name"

# Or make it executable and then run it
chmod +x $JBI_FOLDER/$setup_file_name
chmod +x $JBI_FOLDER/$env_file_name

echo "export PATH=\"\$PATH:\$HOME/.jbi/env_variables.sh"\" >> ~/test

$JBI_FOLDER/$setup_file_name
echo 
source "$HOME/.zshrc"
