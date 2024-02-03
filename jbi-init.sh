
#Install Command
# /bin/bash -c "$(curl -fsSL https://github.com/MichaelOC23/setup/tree/main/jbi-setup.sh)"

#Custom hidden root folder for JBI machines to install software

JBI_FOLDER = "$HOME/.jbi"
mkdir -p $JBI_FOLDER

file_name="jbi-setup.sh"

url="https://github.com/MichaelOC23/setup/tree/main/jbi-setup.sh"

# Use curl to download the file
curl -L $url -o "$JBI_FOLDER/$file_name"

# Or make it executable and then run it
chmod +x $JBI_FOLDER/$file_name
$destination_folder/$file_name
