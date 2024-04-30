#!/bin/bash

# Get the current working directory
current_dir=$(pwd)

# Extract the parent directory name
parent_dir_name=$(basename "$current_dir")

# Get current date and time in YYYYMMDD_HHMMSS format
current_date=$(date +%Y%m%d_%H%M%S)

# Define the filename as the parent directory name followed by the current date and time
filename="${parent_dir_name}_${current_date}.txt"

# Create an empty file with the defined filename
touch "$filename"

# Initialize a temporary file to store extensions
tmpfile=$(mktemp)

# Iterate over all files in the current directory and its subdirectories
find "$current_dir" -type f | while read -r file; do
    # Append the full path of the file to the created file
    echo "$file" >>"$filename"

    # Extract file extension
    extension="${file##*.}"

    # Write the extension to a temporary file
    echo "$extension" >>"$tmpfile"
done

# Count occurrences of each extension
echo "File type counts:" >>"$filename"
sort "$tmpfile" | uniq -c | while read count extension; do
    echo "$extension: $count" >>"$filename"
done

# Clean up the temporary file
rm "$tmpfile"

# Print completion message
echo "Script execution completed. Results saved to $filename"
