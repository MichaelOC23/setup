#!/bin/bash

# Clear the screen
clear

# Get the service key from the first argument
KEY="$1$2"

# Display the key being used
echo -e "\033[1;97mKey: ${KEY}\033[0m"

# Define the absolute path to the JSON file
JSON_FILE_PATH='/Users/michasmi/.jbi/scripts/test_harness_queries.json'

# Extract the request string using jq, checking for errors
REQUEST=$(jq -r ".${KEY}" "$JSON_FILE_PATH" 2>/dev/null) # Redirect jq errors to /dev/null

if [ $? -ne 0 ] || [ -z "$REQUEST" ]; then # Check for both jq failure and empty result
    echo -e "\033[4;31mERROR: Key '$KEY' not found or empty in '$JSON_FILE_PATH'\033[0m"
    exit 1 # Exit the script if there's an error
fi

# Display service name and JSON payload
echo -e "> > Service Called: \033[4;34m${1}\033[0m || from file: \033[4;34m${JSON_FILE_PATH}\033[0m"
echo -e "> > JSON : \033[1;97m ${REQUEST}\033[0m"

# Send the request via nats (adjust the command as needed)
cd '/Users/michasmi/code/platform/Src/Api' &&
    nats req $1.$2 "$REQUEST" -H Project:CMS -H Token:"$JBIP_KEY" # Use double quotes to preserve spaces in REQUEST
