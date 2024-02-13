#!/bin/bash
# ENV_VARIABLES.sh

#sync with the dashlane cli
dcli sync
export ENV_VAR_LOAD_DATE_TIME=$(date '+%Y-%m-%d %H:%M:%S')

#Key Folder Locations THESE MUST BE CORRECT PER USER
export JBI_FOLDER_PATH="${HOME}/.jbi"
export CODE_FOLDER_PATH="${HOME}/code"
export VSCODE_FOLDER_PATH="${CODE_FOLDER_PATH}/vscode"
export STABLE_FOLDER_PATH="${CODE_FOLDER_PATH}/.stable"
export WORKING_DIRECTORY="${CODE_FOLDER_PATH}/product-tools"
export WORKING_DIRECTORY="${CODE_FOLDER_PATH}/communify"
export CODE_ADMIN_DIRECTORY="${VSCODE_FOLDER_PATH}/code-admin"
#Date and Time for logging

#Notes Folder
NOTE_FOLDER_PATH="$HOME/Library/Mobile Documents/com~apple~CloudDocs/JBI/notes/"

# PATH Export
export PATH=/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin
export PATH="${PATH}:${CODE_ADMIN_DIRECTORY}"
export PATH="${PATH}:${JBI_FOLDER_PATH}"
export PATH="${PATH}:/Applications/geckodriver*"
export PATH="${PATH}:/opt/homebrew/bin/jupyter-lab"
export PATH="${PATH}:${WORKING_DIRECTORY}"
export PATH="${PATH}:${WORKING_DIRECTORY}/shared"

json_string=$(dcli note localeFormat=UNIVERSAL -o json)
# echo "json_string is ${json_string}"

# Ensure 'jq' is available
if ! command -v jq &>/dev/null; then
    echo "jq command could not be found"
    exit 1
fi

# Loop through each entry in the JSON array
echo "$json_string" | jq -c '.[]' | while read -r i; do
    # Extract title and content
    title=$(echo "$i" | jq -r '.title')
    content=$(echo "$i" | jq -r '.content')

    # Export them as environment variables
    export "${title}=${content}"
    echo "Exported ${title} with content length ${#content}"
done
echo "Environment Variable SHOW_ME has value: ${SHOW_ME}"
echo "Environment Variables Updated: ${ENV_VAR_LOAD_DATE_TIME}"

#Streamlit
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10000

# Open AI
export OPENAI_TRANSCRIPTION_ENDPOINT="https://api.openai.com/v1/transcriptions"

# Azure DevOps
export AZURE_DEVOPS_ORG="justbuildit"
export AZURE_PROJECT_NAME="OC2Communify"
export AZURE_PROJECT_BASE_URL="https://${AZURE_DEVOPS_ORG}@dev.azure.com/${AZURE_DEVOPS_ORG}/${AZURE_PROJECT_NAME}/_git"
export AZURE_AUTH_HEADER="Authorization: Basic $(echo -n "justbuildit.com:${AZURE_DEVOPS_PAT}" | base64)"
export AZURE_PROJECTS_ENDPOINT="https://dev.azure.com/${AZURE_DEVOPS_ORG}/_apis/projects?api-version=6.0"

#Standardize python commands
alias python='python3'
alias pip='pip3'

#Aliases for running Audio Transcription
alias Audio="${VSCODE_FOLDER_PATH}/cool-tools/cool_venv/bin/python ${VSCODE_FOLDER_PATH}/cool-tools/_Audio.py"
alias AudioStop="echo 1 > ${VSCODE_FOLDER_PATH}/cool-tools/working/stopfile.txt"
