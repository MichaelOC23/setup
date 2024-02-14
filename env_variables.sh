#!/bin/bash
# ENV_VARIABLES.sh

# Capture and print the current time:
export ENV_VAR_LOAD_DATE_TIME=$(date '+%Y-%m-%d %H:%M:%S')

#sync with the dashlane cli. This updates the secrets to be stored locally
dcli sync

#Get all the locally stored secrets
json_string=$(dcli note localeFormat=UNIVERSAL -o json)
echo "\033[1;34m > json_string with secrets \033[0;32m Successfully Obtained. \033[0m"
#echo "json_string is ${json_string}"

# Ensure 'jq' is available (JSON Parser)
if ! command -v jq &>/dev/null; then
    echo "\033[0;31m !!! jq (JSON Parser) command could not be found. It is required to obtain the secrets.\033[0m"
    exit 1
else
    echo -e "\033[1;34m > jq (JSON Parser) command is: \033[0;32m ** Present **.  \033[0m"
fi

SECRET_TITLES=""

# Loop through each entry in the JSON array
echo "$json_string" | jq -c '.[]' | while read -r i; do
    # Extract title and content
    title=$(echo "$i" | jq -r '.title')
    content=$(echo "$i" | jq -r '.content')

    # Export them as environment variables
    export "${title}=${content}"

    #Concatenate the titles of the secets into the SECRET_TITLES variable
    SECRET_TITLES="${SECRET_TITLES} ${title}"

done

#Check if $SHOW_ME exists and is set to 123456. if so echo a green message else a red message
if [ -n "${SHOW_ME}" ] && [ "${SHOW_ME}" = "123456" ]; then
    echo -e "\033[0;34m > The SHOW_ME value of 123456 is: \033[0;32m CORRECT. This is correct. \033[0m"
    echo -e "\033[0;34m > Date/Time of Secrets load: \033[0;32m${ENV_VAR_LOAD_DATE_TIME} \033[0m"
else
    echo -e "\033[0;31m > The value of SHOW_ME is not 123456. It is ${SHOW_ME}. This is incorrect. \033[0m"
    exit 1
fi

#Key Folder Locations
export JBI_FOLDER_PATH="${HOME}/.jbi"                                      # "#Key Folder Locations THESE MUST BE CORRECT"
export CODE_FOLDER_PATH="${HOME}/code"                                     # "#Key Folder Locations THESE MUST BE CORRECT"
export VSCODE_FOLDER_PATH="${CODE_FOLDER_PATH}/vscode"                     # "#Key Folder Locations THESE MUST BE CORRECT"
export STABLE_FOLDER_PATH="${CODE_FOLDER_PATH}/.stable"                    # "#Key Folder Locations THESE MUST BE CORRECT"
export PRODUCT_FOLDER_PATH="${CODE_FOLDER_PATH}/product-tools"             # "#Key Folder Locations THESE MUST BE CORRECT"
export COMMUNIFY_FOLDER_PATH="${CODE_FOLDER_PATH}/communify"               # "#Key Folder Locations THESE MUST BE CORRECT"
export COMMUNIFY_SHARED_FOLDER_PATH="${CODE_FOLDER_PATH}/communify/shared" # "#Key Folder Locations THESE MUST BE CORRECT"
export CODE_ADMIN_FOLDER_PATH="${CODE_FOLDER_PATH}/code-admin"             # "#Key Folder Locations THESE MUST BE CORRECT"

export JBI_FOLDER_PATH="$HOME/Library/Mobile Documents/com~apple~CloudDocs/JBI"                             # "Communify files (non-code files)"
export COMMUNIFY_FOLDER_PATH="$HOME/Library/Mobile Documents/com~apple~CloudDocs/JBI/communify"             # "Communify files (non-code files)"
export COMMUNIFY_NOTES_FOLDER_PATH="$HOME/Library/Mobile Documents/com~apple~CloudDocs/JBI/communify/notes" # "Communify files (non-code files)"
export COMMUNIFY_IO_FOLDER_PATH="$HOME/Library/Mobile Documents/com~apple~CloudDocs/JBI/communify/in-out"   # "Communify files (non-code files)"

# PATH export
export PATH="/System/Cryptexes/App/usr/bin:/usr/bin:/bin" # Standard Path
export PATH="${PATH}:/usr/sbin:/sbin:/usr/local/bin"      # Standard Path

# Add additional locations to the PATH
export PATH="${PATH}:/opt/homebrew/bin:/opt/homebrew/sbin" # Homebrew
export PATH="${PATH}:/Applications/geckodriver*"           # For Scraping
export PATH="${PATH}:/opt/homebrew/bin/jupyter-lab"        # For Jupier Lab
export PATH="${PATH}:${STABLE_FOLDER_PATH}"                # This allows easy running of either stable or communify code
export PATH="${PATH}:${COMMUNIFY_FOLDER_PATH}"             # This allows easy running of either stable or communify code
export PATH="${PATH}:${COMMUNIFY_SHARED_FOLDER_PATH}"      # This allows all the files in main communify folder to include shared libraries in the shared folder
export PATH="${PATH}:${CODE_ADMIN_FOLDER_PATH}"            # This is mostly a dev area for script. It's nice to be able to run them without typing the full path.

# Set the default editor to Visual Studio Code
export EDITOR="code"

# Set the colors for the terminal
export RED="\033[0;31m"
export GREEN="\033[0;32m"
export BLUE="\033[0;34m"
export ORANGE="\033[0;33m"
export PURPLE="\033[0;35m"
export CYAN="\033[0;36"
export YELLOW="\033[1;33m"
export WHITE="\033[1;37m"
export LIGHT_GRAY="\033[0;37m"
export LIGHT_BLUE="\033[1;34m"
export END_COLOR="\033[0m" # No Color

export LOG_LEVEL="LIGHT" # "Used to trigger heavier logging and print statements for debugging options are: LIGHT or VERBOSE"

#Streamlit
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10000

#Dev / AI
export OPENAI_TRANSCRIPTION_ENDPOINT="https://api.openai.com/v1/transcriptions"                                          # "Open AI"
export AZURE_DEVOPS_ORG="justbuildit"                                                                                    # "Azure DevOps"
export AZURE_PROJECT_NAME="OC2Communify"                                                                                 # "Azure DevOps"
export AZURE_PROJECT_BASE_URL="https://${AZURE_DEVOPS_ORG}@dev.azure.com/${AZURE_DEVOPS_ORG}/${AZURE_PROJECT_NAME}/_git" # "Azure DevOps"
export AZURE_AUTH_HEADER="Authorization: Basic $(echo -n justbuildit.com:${AZURE_DEVOPS_PAT})"                           # "Azure DevOps"
export AZURE_PROJECTS_ENDPOINT="https://dev.azure.com/${AZURE_DEVOPS_ORG}/_apis/projects?api-version=6.0"                # "Azure DevOps"

#Ensure key directories exist for Communify
mkdir -p ${JBI_FOLDER_PATH}
mkdir -p ${COMMUNIFY_FOLDER_PATH}
mkdir -p ${COMMUNIFY_NOTES_FOLDER_PATH}
mkdir -p ${COMMUNIFY_IO_FOLDER_PATH}

#Standardize python commands
alias python='python3'
alias pip='pip3'

# ADD LATER: Aliases for running Audio Transcription
# alias Audio= ${VENV_PATH}/venv/bin/python ${PATH TO Audio.py}
# alias AudioStop= echo 1 > ${stop path}

# If the log level is set to VERBOSE then print all the environment variables
if [ "${LOG_LEVEL}" = "VERBOSE" ]; then
    echo -e "\033[0;34m > All Environment Variables: \033[0;32m"
    env
    echo -e "\033[0m"
fi
