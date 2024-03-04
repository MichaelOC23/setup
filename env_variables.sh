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
    echo -e "\033[1;34m > jq (JSON Parser) command is: \033[3;32m ** Present **.  \033[0m"
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
    echo -e "\033[0;34m > The SHOW_ME value of 123456 is: \033[0;32m **  CORRECT  ** \033[0m"
    echo -e "\033[0;34m > Date/Time of Secrets load: \033[0;32m  **  ${ENV_VAR_LOAD_DATE_TIME}  ** \033[0m"
else
    echo -e "\033[0;31m > The value of SHOW_ME is not 123456. It is ${SHOW_ME}. This is incorrect. \033[0m"
    exit 1
fi

#Key Folder Locations for python scripts and projects
export CODE_FOLDER_PATH="${HOME}/code"                                       # "#Key Folder Locations THESE MUST BE CORRECT"
export VSCODE_FOLDER_PATH="${CODE_FOLDER_PATH}/vscode"                       # "#Key Folder Locations THESE MUST BE CORRECT"
export STABLE_FOLDER_PATH="${CODE_FOLDER_PATH}/.stable"                      # "#Key Folder Locations THESE MUST BE CORRECT"
export PRODUCT_FOLDER_PATH="${CODE_FOLDER_PATH}/product-tools"               # "#Key Folder Locations THESE MUST BE CORRECT"
export COMMUNIFY_FOLDER_PATH="${CODE_FOLDER_PATH}/communify"                 # "#Key Folder Locations THESE MUST BE CORRECT"
export COMMUNIFY_SHARED_FOLDER_PATH="${CODE_FOLDER_PATH}/communify/shared"   # "#Key Folder Locations THESE MUST BE CORRECT"
export CODE_ADMIN_FOLDER_PATH="${CODE_FOLDER_PATH}/code-admin"               # "#Key Folder Locations THESE MUST BE CORRECT"
export PERSONAL_EXPENSES_FOLDER_PATH="${CODE_FOLDER_PATH}/personal-expenses" # "#Key Folder Locations THESE MUST BE CORRECT"

#KEY IO Folder Locations
export IO_FOLDER_PATH="${HOME}/Library/Mobile Documents/com~apple~CloudDocs/jbi" # "File in-out temp folder (general)
export COMMUNIFY_IO_FOLDER_PATH="${IO_FOLDER_PATH}/communify"                    # "File in-out temp folder (communify)
export NOTES_IO_FOLDER_PATH="${IO_FOLDER_PATH}/notes"                            # "File in-out temp folder (Notes)
export AUDIO_IO_FOLDER_PATH="${IO_FOLDER_PATH}/audio"                            # "File in-out temp folder (Audio)
export IMAGES_IO_FOLDER_PATH="${IO_FOLDER_PATH}/images"                          # "File in-out temp folder (Images)
export TEMP_IO_FOLDER_PATH="${IO_FOLDER_PATH}/temp"                              # "File in-out temp folder (Temp)
export TRANSCRIPTIONS_IO_FOLDER_PATH="${IO_FOLDER_PATH}/transcriptions"          # "File in-out temp folder (Transcriptions)
export SCRAPED_CONTENT_IO_FOLDER_PATH="${IO_FOLDER_PATH}/scraped-content"        # "File in-out temp folder (Scraped Content from Websites)
export LOGS_IO_FOLDER_PATH="${IO_FOLDER_PATH}/logs"                              # "File in-out temp folder (Logs)
export PROMPTS_IO_FOLDER_PATH="${COMMUNIFY_FOLDER_PATH}/prompts"                 # "File in-out temp folder (Prompts)
export LLM_IO_FOLDER_PATH="${IO_FOLDER_PATH}/llm"                                # "File in-out temp folder (Large Language Models)
export EMAIL_IO_FOLDER_PATH="${IO_FOLDER_PATH}/email"                            # "File in-out temp folder (Email)
export PERSONAL_EXPENSES_IO_FOLDER_PATH="${IO_FOLDER_PATH}/personal-expenses"    # "File in-out temp folder (Personal Expenses)
export DOWJONES_IO_FOLDER_PATH="${IO_FOLDER_PATH}/dowjones"                      # "File in-out temp folder (Large Language Models)

#Ensure key IO directories exist
mkdir -p ${IO_FOLDER_PATH}
mkdir -p ${COMMUNIFY_IO_FOLDER_PATH}
mkdir -p ${NOTES_IO_FOLDER_PATH}
mkdir -p ${AUDIO_IO_FOLDER_PATH}
mkdir -p ${IMAGES_IO_FOLDER_PATH}
mkdir -p ${TEMP_IO_FOLDER_PATH}
mkdir -p ${TRANSCRIPTIONS_IO_FOLDER_PATH}
mkdir -p ${SCRAPED_CONTENT_IO_FOLDER_PATH}
mkdir -p ${LOGS_IO_FOLDER_PATH}
mkdir -p ${PROMPTS_IO_FOLDER_PATH}
mkdir -p ${LLM_IO_FOLDER_PATH}
mkdir -p ${DOWJONES_IO_FOLDER_PATH}
mkdir -p ${EMAIL_IO_FOLDER_PATH}
mkdir -p ${PERSONAL_EXPENSES_IO_FOLDER_PATH}
mkdir -p ${DOWJONES_IO_FOLDER_PATH}

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
export PATH="${PATH}:${PERSONAL_EXPENSES_FOLDER_PATH}"     # There are a number of libraries here that need their own folder to not lose track of them

# Set the default editor to Visual Studio Code
export EDITOR="code"

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

#Standardize python commands
export PATH="/opt/homebrew/bin:$PATH"
alias python='python3'
alias pip='pip3'
alias llmstart="cd ${COMMUNIFY_FOLDER_PATH} && llm_launch.sh"
alias llmstop="cd ${COMMUNIFY_FOLDER_PATH} && llm_launch.sh stop"

# ADD LATER: Aliases for running Audio Transcription
# alias Audio= ${VENV_PATH}/venv/bin/python ${PATH TO Audio.py}
# alias AudioStop= echo 1 > ${stop path}

# If the log level is set to VERBOSE then print all the environment variables
if [ "${LOG_LEVEL}" = "VERBOSE" ]; then
    echo -e "\033[0;34m > All Environment Variables: \033[0;32m"
    env
    echo -e "\033[0m"
fi

# alias python="/opt/homebrew/bin/python3.12"
# alias python3="/opt/homebrew/bin/python3.12"
# alias pip="/opt/homebrew/bin/pip3"
