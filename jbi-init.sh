
#Custom hidden root folder for JBI machines to install software

JBI_FOLDER = "$HOME/.jbi"
mkdir -p $JBI_FOLDER

destination_folder="/path/to/destination/folder"
file_name="jbi-setup.sh"

url="https://raw.githubusercontent.com/user/repo/branch/path/to/file.sh"

# Define the destination folder
destination_folder="/path/to/destination/folder"

# Use curl to download the file
curl -L $url -o $destination_folder/file.sh


# Run the script with bash
bash $destination_folder/$file_name

# Or make it executable and then run it
chmod +x $destination_folder/$file_name
$destination_folder/$file_name
