#!/bin/bash
# ENV_VARIABLES.sh

# Capture and print the current time:
export ENV_VAR_LOAD_DATE_TIME=$(date '+%Y-%m-%d %H:%M:%S')
export PGPORT=4999

#sync with the dashlane cli. This updates the secrets to be stored locally
dcli sync

#Get all the locally stored secrets
json_string=$(dcli note localeFormat=UNIVERSAL -o json)
echo "\033[1;34m > json_string with secrets \033[0;32m Successfully Obtained. \033[0m"
# echo "json_string is ${json_string}"

# Ensure 'jq' is available (JSON Parser)
if ! command -v jq &>/dev/null; then
    echo "\033[0;31m !!! jq (JSON Parser) command could not be found. It is required to obtain the secrets.\033[0m"
    exit
else
    echo -e "\033[1;34m > jq (JSON Parser) command is: \033[3;32m ** Present **.  \033[0m"
fi

# Define the paths to the .env files
env_file1="${HOME}/code/mytech/.env"
env_file2="${HOME}/.jbi/.env"

SECRET_TITLES=""
# Loop through each entry in the JSON array
echo "$json_string" | jq -c '.[]' | while read -r i; do
    # Extract title and content
    title=$(echo "$i" | jq -r '.title')
    content=$(echo "$i" | jq -r '.content')

    # Export them as environment variables
    export "${title}=${content}"

    # Append to SECRET_TITLES
    SECRET_TITLES="${SECRET_TITLES}\n${title}=${content}"
done

# Write SECRET_TITLES and all secrets to the .env file
echo -e "SECRET_TITLES=${SECRET_TITLES}" >"$env_file1"
echo -e "SECRET_TITLES=${SECRET_TITLES}" >"$env_file2"

echo -e "\033[0;34m > Updated \033[0;32m ${env_file1} \033[0m."
echo -e "\033[0;34m > Updated \033[0;32m ${env_file2} \033[0m."

#Check if $SHOW_ME exists and is set to 123456. if so echo a green message else a red message
if [ -n "${SHOW_ME}" ] && [ "${SHOW_ME}" = "123456" ]; then
    echo -e "\033[0;34m > The SHOW_ME value of 123456 is: \033[0;32m **  CORRECT  ** \033[0m"
    echo -e "\033[0;34m > Date/Time of Secrets load: \033[0;32m  **  ${ENV_VAR_LOAD_DATE_TIME}  ** \033[0m"
else
    echo -e "\033[0;31m > The value of SHOW_ME is not 123456. It is ${SHOW_ME}. This is incorrect. \033[0m"
    exit
fi

#Standardize python commands
alias python='python3'
alias pip='pip3'

#Key Folder Locations for python scripts and projects
export NVM_DIR=/opt/homebrew/Cellar/nvm/0.39.7

# PATH export (Standard mack path)
export PATH="/System/Cryptexes/App/usr/bin:/usr/bin:/bin" # Standard Path
export PATH="${PATH}:/usr/sbin:/sbin:/usr/local/bin"      # Standard Path

# Add additional locations to the PATH
export PATH="/opt/homebrew/bin:/opt/homebrew/sbin:$PATH" # Homebrew (prioritizing it over the system python)
export PATH="${PATH}:${HOME}/.jbi/scripts"
export PATH="${PATH}:${HOME}/.jbi/classes"          # personal scripts
export PATH="${PATH}:/Applications/geckodriver*"    # For Scraping
export PATH="${PATH}:/opt/homebrew/bin/jupyter-lab" # For Jupiter Lab

# Personal custom classes
export PYTHONPATH="${HOME}/.jbi/classes"
export PYTHONPATH="${PYTHONPATH}:${HOME}/.jbi/classes/_class_streamlit.py"
export PYTHONPATH="${PYTHONPATH}:${HOME}/.jbi/classes/_class_extract_text.py"
export PYTHONPATH="${PYTHONPATH}:${HOME}/.jbi/classes/_class_ollama.py"
export PYTHONPATH="${PYTHONPATH}:${HOME}/.jbi/classes/_class_BMM.py"
export PYTHONPATH="${PYTHONPATH}:${HOME}/.jbi/classes/_class_storage.py"
export PYTHONPATH="${PYTHONPATH}:${HOME}/.jbi/classes/_class_dow_jones.py"
export PYTHONPATH="${PYTHONPATH}:${HOME}/.jbi/classes/_class_pe_categorize_transactions.py"
export PYTHONPATH="${PYTHONPATH}:${HOME}/.jbi/classes/_class_search_web.py"

# Set the default editor to Visual Studio Code
export EDITOR="code"

# export LOG_LEVEL="LIGHT" # "Used to trigger heavier logging and print statements for debugging options are: LIGHT or VERBOSE"

#Streamlit
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10000

# OpenAI
export OPENAI_TRANSCRIPTION_ENDPOINT="https://api.openai.com/v1/transcriptions"

# Azure
# export AZURE_DEVOPS_ORG="justbuildit"                                                                                    # "Azure DevOps"
# export AZURE_PROJECT_NAME="OC2Communify"                                                                                 # "Azure DevOps"
# export AZURE_PROJECT_BASE_URL="https://${AZURE_DEVOPS_ORG}@dev.azure.com/${AZURE_DEVOPS_ORG}/${AZURE_PROJECT_NAME}/_git" # "Azure DevOps"
# export AZURE_AUTH_HEADER="Authorization: Basic $(echo -n justbuildit.com:${AZURE_DEVOPS_PAT})"                           # "Azure DevOps"
# export AZURE_PROJECTS_ENDPOINT="https://dev.azure.com/${AZURE_DEVOPS_ORG}/_apis/projects?api-version=6.0"                # "Azure DevOps"

##### NGROK#####
# Get the ngrok public URL
# Make the curl request and use jq to parse the JSON response, extracting the public_url
NGROK_PUBLIC_URL=$(curl -s \
    -X GET \
    -H "Authorization: Bearer ${NGROK_API_KEY}" \
    -H "Ngrok-Version: 2" \
    "https://api.ngrok.com/endpoints" | jq -r '.endpoints[0].public_url')
# Export the public URL as an environment variable
echo "Extracted Public URL: $NGROK_PUBLIC_URL"
export NGROK_PUBLIC_URL

# Now, NGROK_PUBLIC_URL is available as an environment variable in this script's execution context
# To use it in other terminal sessions or scripts, you might need to source this script or handle it differently

#Color Variables for text
BLACK='\033[0;30m'
RED='\033[0;31m'
RED_U='\033[4;31m'
RED_BLINK='\033[5;31m'
GREEN='\033[0;32m'
GREEN_BLINK='\033[5;32m'
YELLOW='\033[0;33m'
YELLOW_BOLD='\033[1;33m'
PURPLE='\033[1;34m'
PURPLE_U='\033[4;34m'
PURPLE_BLINK='\033[5;34m'
PINK='\033[0;35m'
PINK_U='\033[4;35m'
PINK_BLINK='\033[5;35m'
LIGHTBLUE='\033[0;36m'
LIGHTBLUE_BOLD='\033[1;36m'
GRAY='\033[0;37m'
ORANGE='\033[1;91m'
BLUE='\033[1;94m'
CYAN='\033[1;96m'
WHITE='\033[1;97m'
MAGENTA='\033[1;95m'
BOLD='\033[1m'
UNDERLINE='\033[4m'
BLINK='\033[5m'
NC='\033[0m' # No Color
