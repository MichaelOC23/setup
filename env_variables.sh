#!/bin/bash
# ENV_VARIABLES.sh

#sync with the dashlane cli
dcli sync 

#Date and Time for logging
export ENV_VAR_LOAD_DATE_TIME=$(date '+%Y-%m-%d %H:%M:%S')


json_string=$(dcli note localeFormat=UNIVERSAL -o json)
#echo $json_string

# Loop through each entry in the JSON array
echo $json_string | jq -c '.[]' | while read -r i; do
    # Extract title and content
    title=$(echo $i | jq -r '.title')
    content=$(echo $i | jq -r '.content')

    # Export them as environment variables
    export "$title=$content"
    #echo "Exported $title=$content"
done
echo "Environment Variable SHOW_ME has value: $SHOW_ME"
echo "Environment Variables Updated: $ENV_VAR_LOAD_DATE_TIME"

export WORKING_DIRECTORY="/Volumes/code/vscode/cool-tools/"

# PATH Export
export PATH=/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/System/Cryptexes/App/usr/bin:/usr/bin:/bin:/usr/sbin:/sbin
export PATH="$PATH:/Volumes/code/vscode/code-admin/scripts/"
export PATH="$PATH:/Applications/geckodriver*"
export PATH="$PATH:/opt/homebrew/bin/jupyter-lab"
export PATH="$PATH:$WORKING_DIRECTORY"
export PATH="$PATH:$WORKING_DIRECTORY/shared"

#JBI Scripts
export PATH="$HOME/.jbi:$PATH"

#Streamlit
export STREAMLIT_SERVER_MAX_UPLOAD_SIZE=10000

#Key Folder Locations
export VSCODE_FOLDER_PATH="/Volumes/code/vscode"

# Open AI
export OPENAI_TRANSCRIPTION_ENDPOINT="https://api.openai.com/v1/transcriptions"

# Azure DevOps
export AZURE_DEVOPS_ORG="outercirclesdev"
export AZURE_PROJECT_NAME="vscode-dev"
export AZURE_PROJECT_BASE_URL="https://$AZURE_DEVOPS_ORG@dev.azure.com/$AZURE_DEVOPS_ORG/$AZURE_PROJECT_NAME/_git"
export AZURE_AUTH_HEADER="Authorization: Basic $(echo -n "michael@outercircles.com:$AZURE_DEVOPS_PAT" | base64)"
export AZURE_PROJECTS_ENDPOINT="https://dev.azure.com/$AZURE_DEVOPS_ORG/_apis/projects?api-version=6.0"

#Standardize python commands
alias python='python3'
alias pip='pip3'

#Aliases for running Audio Transcription
alias Audio="$VSCODE_FOLDER_PATH/cool-tools/cool_venv/bin/python $VSCODE_FOLDER_PATH/cool-tools/_Audio.py"
alias AudioStop="echo 1 > $VSCODE_FOLDER_PATH/cool-tools/working/stopfile.txt"


