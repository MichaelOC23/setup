#!/bin/bash

# Check if the directory parameter is provided
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory>"
    exit 1
fi

# Assign the parameter to a variable
dir=$1

# Check if the specified directory exists
if [ ! -d "$dir" ]; then
    echo "Error: The directory $dir does not exist."
    exit 1
fi

# Navigate to the specified directory
cd "$dir" || { echo "Error: Failed to change directory to $dir"; exit 1; }

# Find all .git directories, .gitignore and .gitattributes files and remove them
find . \( -type d -name ".git" -o -name ".gitignore" -o -name ".gitattributes" \) | while read -r gititem; do
    if [[ -d "$gititem" ]]; then
        # It's a .git directory
        rm -rf "$gititem"
        echo "Removed Git repository in $(dirname "$gititem")"
    else
        # It's a file
        rm -f "$gititem"
        echo "Removed $gititem"
    fi
done
