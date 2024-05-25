#!/bin/bash

# Check if the user has provided an argument
if [ $# -eq 0 ]; then
    echo "Usage: $0 <filename>"
    exit 1
fi

# The filename is the first argument
filename="$1"

# Use head to get the first 5 lines of the file
head -n 5 "$filename" > "${filename%.csv}_first_5_rows.csv"

echo "First 5 rows of $filename have been saved to ${filename%.csv}_first_5_rows.csv"

