#!/bin/bash

# Generate a timestamp for the log file name
timestamp=$(date +"%m%d%Y_%H%M%S")
log_file="/Users/michasmi/logs/commit_log_${timestamp}.txt"

# Key folders
CODE_FOLDER_PATH="${HOME}/code"

{
    echo

    commit_current_folder() {

        echo "Committing changes to current repository at: $PWD"
        git pull origin main
        git add .
        git commit -m "default commit message"
        git push origin main

        if [ $? -eq 0 ]; then
            echo -e "Commit Successful for ${PWD}"
        else
            echo -e "!! ERROR !! Commit was not successful"
        fi

    }

    echo "You chose Option 1: Commit and Push All: VSCODE .JBI COMMUNIFY\n"
    echo "Committing and pushing $CODE_FOLDER_PATH"

    # Navigate to the directories and commit
    cd "$CODE_FOLDER_PATH/communify" || exit
    commit_current_folder

    cd "$CODE_FOLDER_PATH/product-tools" || exit
    commit_current_folder

    cd "$CODE_FOLDER_PATH/vscode" || exit
    commit_current_folder

    cd "$CODE_FOLDER_PATH/code_admin" || exit
    commit_current_folder

    cd "$HOME/.jbi" || exit
    commit_current_folder

} > "$log_file" 2>&1

code "$log_file"
