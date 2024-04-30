#!/bin/bash

# Check for the correct number of arguments
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <file_extension> <source_directory> <target_directory>"
    exit 1
fi

echo "Copying all files with extension $1 from $2 to $3"

# Assign arguments to variables
file_extension=$1
source_directory=$2
target_directory=$3
error_log="${target_directory}/copy-error.log"

echo "Error log: $error_log"

# Function to copy files
copy_file() {
    local source_file=$1
    local target_file=$2

    if [ -e "$target_file" ]; then
        # File exists, append a number
        local base_name=$(basename -- "$target_file")
        local name="${base_name%.*}"
        local extension="${base_name##*.}"
        local counter=1

        while [ -e "${target_directory}/${name}_$(printf "%03d" $counter).${extension}" ]; do
            ((counter++))
        done

        target_file="${target_directory}/${name}_$(printf "%03d" $counter).${extension}"
    fi

    # Try to copy and log errors if any
    cp "$source_file" "$target_file" 2>>"$error_log" || echo "Failed to copy $source_file" >>"$error_log"
}

# Export function and variables for use with 'find' command
export -f copy_file
export file_extension
export target_directory
export error_log

# Find and copy files
find "$source_directory" -type f -name "*.$file_extension" -exec bash -c 'copy_file "$0" "${target_directory}/$(basename "$0")"' {} \;
