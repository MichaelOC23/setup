#!/bin/bash

# This sources all the functions in the ms_mac_functions.sh file
# These will be used to perform the actions in the menu
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
echo "Script directory: $script_dir"
# Initial full path
FULL_PATH="Users/michasmi/code/vscode/code-admin/scripts"
#/Volumes/code/vscode/code-admin/scripts"

# Navigate up two levels
VSCODE_PATH=$(dirname $(dirname "$script_dir"))

# Print the result
echo "VSCode path: $VSCODE_PATH"

COMMUNIFY_PATH="$CODE_FOLDER_PATH/communify"
PRODUCT_TOOLS_PATH="$CODE_FOLDER_PATH/product-tools"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;31m'
NC='\033[0m' # No Color

# Function to display the menu
show_menu() {
    echo -e "\n\nHello! What would you like to do?"
    echo -e "Please choose one of the following options (enter the number):\n"
    echo -e "|-------------------------------------------------------------|\n"

    echo -e "0) Commit the current repository\n"
    echo -e "1) Commit and Push All: VSCODE .JBI COMMUNIFY\n"
    echo -e "2) Start / Restart Stable Tools\n"
    echo -e "3) Start Doccano\n"
    # echo -e "4) Update .zshrc\n"
    # echo -e "5) Edit default .zshrc file\n"
    # echo -e "6) Edit default .gitignore file\n"
    echo -e "7) Restart Postgres 14\n"
    # echo -e "8) launch e2aserver\n"
    # echo -e "9) Launch stable\n"
    echo -e "10) Create/replace .jbi symbolic links\n"
    echo -e "101) Rotate Encryption Keys\n"
    echo -e "1977) Deinitialize vscode\n"
    echo -e "2008) DISCARD all changes and REPLACE with latest version from Azure Devops\n"

}

commit_current_folder() {

    echo "Comitting changes to current repository at: $pwd"
    git pull origin main
    git add .
    git commit -m "default commit message"
    git push origin main

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Commit Successful for $PWD ${NC}"
    else
        echo -e "${RED}!! ERROR !! Commit was not successful${NC}"
    fi

}
# Function to read the user's choice
read_choice() {
    local choice
    read -p "Enter choice [1 - 8]: " choice
    case $choice in
    1000)
        nano /Volumes/code/vscode/code-admin/scripts/menu.sh
        ;;

    0)
        echo "You chose Option 0"
        commit_current_folder
        ;;

    1)
        echo "You chose Option 1: Commit and Push All: VSCODE .JBI COMMUNIFY\n"
        echo "Committing and pushing $VSCODE_FOLDER_PATH"
        # Navigate to ~/vsce
        cd "$CODE_FOLDER_PATH/communify" || exit
        commit_current_folder

        cd "$CODE_FOLDER_PATH/product-tools" || exit
        commit_current_folder

        cd $HOME/.jbi || exit
        commit_current_folder

        ;;

    2)
        echo "Update and Start Product Tools"

        # Check if app.py is running
        APP_PY_PID=$(pgrep -f "streamlit run 000_Communify_Home")

        if [ -n "$APP_PY_PID" ]; then
            echo "app.py is running. Stopping it..."
            kill $APP_PY_PID
        fi

        cd "$HOME/code"
        rm -rf .stable
        mkdir -p .stable
        STABLE_DIR="$HOME/code/.stable"
        cd $STABLE_DIR

        git clone "https://michael:$AZURE_DEVOPS_PAT@dev.azure.com/$AZURE_DEVOPS_ORG/product-development/_git/communify"
        cd communify
        ./env_setup.sh

        cd $STABLE_DIR

        git clone "https://michael:$AZURE_DEVOPS_PAT@dev.azure.com/$AZURE_DEVOPS_ORG/product-development/_git/product-tools"
        cd product-tools
        ./env_setup.sh

        # Relaunch app.py with streamlit
        echo "Relaunching app.py with streamlit..."
        source "$HOME/code/.stable/communify/communify_venv/bin/activate" && streamlit run "$HOME/code/.stable/communify/000_Communify_Home.py"

        ;;

    3)
        echo "Starting Doccano"
        # Activate the virtual environment
        source "$VSCODE_PATH/doccano/doccano_venv/bin/activate"

        # Start the doccano task in the background
        doccano task &
        echo "Doccano task started. Waiting for 3 seconds..."
        sleep 3

        # Start the doccano webserver on port 8000 in the background
        doccano webserver --port 8000 &
        echo "Starting Doccano webserver. Waiting for 3 seconds..."
        sleep 3

        # Optional: add a wait command if you want the script to wait for these processes to finish
        # wait

        echo "Doccano tasks started."
        ;;

    4)
        echo "Start Product-Tools (Development Folder Port: 85)"
        source "$HOME/code/communify/communify_venv/bin/activate" && streamlit run "$HOME/code/communify/000_Communify_Home.py"
        ;;
    5)
        echo "EMPTY"
        echo "EMPTY"
        ;;
    6)
        echo "EMPTY"
        ;;
    7)
        echo "Restarting Postgres 14"
        brew services restart postgresql@14
        echo "Postgres 14 restarted"
        ;;
    8)
        echo "EMPTY"
        # # if e2aserver is running, stop it
        # if docker ps | grep -q e2aserver; then
        #     echo "e2aserver is running. Stopping it now."
        #     docker stop e2aserver
        #     docker rm e2aserver
        # fi
        # cd /Volumes/code/vscode/docker/e2aserver/
        # docker build -t e2aserver .
        # docker run --name e2aserver -p 5678:5678 -p 8000:8000 --rm -v $(pwd):/app e2aserver
        # exit 0
        ;;

    9)
        echo "EMPTY"
        ;;

    10)
        echo "Creating/Replacing .jbi symbolic links"

        #clone the mac setup folder
        rm -rf ~/code/macsetup
        git clone https://justbuildit@dev.azure.com/justbuildit/product/_git/macsetup ~/code/macsetup/

        #Create the .jbi folder and link it to the jbi folder in the code-admin repo
        rm -rf ~/.jbi
        ln -s ~/code/macsetup/ ~/jbi
        mv ~/jbi ~/.jbi

        ;;

    101)
        echo "rotating encryption keys"
        # rotating disposable encryption key
        echo "Old key: $ROTATING_ENCRYPTION_KEY"
        python3 /Volumes/code/vscode/code-admin/gen-enc-key.py
        echo "New key: $ROTATING_ENCRYPTION_KEY"
        exit 0
        ;;

    1977)
        echo -e "\nYou chose Option 2:"
        echo "You are about to deinitialize $VSCODE_FOLDER_PATH"
        # Example usage of the confirm function
        if confirm "Do you want to proceed?"; then
            echo "Beginning deinitialization of $VSCODE_FOLDER_PATH"
            find "$HOME/code/vscode/" -type d -name ".git" -exec rm -rf {} \;
            echo "Deinitialization of $VSCODE_FOLDER_PATH complete."
        else
            echo "Returning to menu."

        fi
        ;;

    2008)
        echo -e "#### WARNING ####"
        echo -e "#### WARNING ####\n"
        echo -e "You are about to DESTROY all changes and"
        echo -e "replace them with the latest version in:"
        echo -e "$pwd\n"
        echo -e "#### THIS CANNOT BE UNDONE ####"
        if confirm "Do you want to proceed?"; then
            git checkout -- .
            git reset --hard
            git fetch origin
            git reset --hard origin/main
        else
            echo "Returning to menu."
        fi

        ;;

    *)
        echo "Invalid choice. Exiting ..."
        exit 0
        ;;

    esac
}

# Function to ask for confirmation
confirm() {
    while true; do
        read -p "$1 (y/n): " yn
        case $yn in
        [Yy]*) return 0 ;;                    # User responded yes
        [Nn]*) return 1 ;;                    # User responded no
        *) echo "Please answer yes or no." ;; # Invalid response
        esac
    done
}

# Function to deinitialize a Git repository
deinitialize_git_repo() {
    if [ -d "$1/.git" ]; then
        # Remove the .git folder to de-initialize the repository
        rm -rf "$1/.git"
        cp /Volumes/code/vscode/code-admin/scripts/gitignore_template $1/.gitignore
        echo "$1 has been de-initialized and the .gitingore file has been resete to the template version."
    fi
}

# Main logic loop
while true; do
    show_menu
    read_choice
done

# new_repo_url="$AZURE_PROJECT_BASE_URL/vscode"
# echo "Repo URL: $new_repo_url"
# if [ ! -d .git ]; then
#     # Initialize the folder as a git repository
#     echo "Initializing $VSCODE_FOLDER_PATH as a git repository"
#     git init
#     git remote add origin $new_repo_url
# fi
