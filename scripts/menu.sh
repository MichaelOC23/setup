#!/bin/bash

# echo "VSCode path: $VSCODE_PATH"

clear

#Key folders
CODE_FOLDER_PATH="${HOME}/code"
JBI_FOLDER_PATH="${HOME}/.jbi"
COMMUNIFY_PATH="${CODE_FOLDER_PATH}/communify"
PRODUCT_TOOLS_PATH="${CODE_FOLDER_PATH}/product-tools"
CODE_ADMIN_PATH="${CODE_FOLDER_PATH}/code-admin"

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

# Function to display the menu
show_menu() {
    echo -e "\n\n${LIGHTBLUE_BOLD}Hello! What would you like to do?"
    echo -e "Please choose one of the following options (enter the number):\n"
    echo -e "|-------------------------------------------------------------|${NC}\n"

    echo -e "${GREEN}0) Commit the current repository${NC}"
    echo -e "${YELLOW}1) Commit and Push MyTech and .JBI ${NC}"
    echo -e "${PINK}2) Start ListGen ${NC}"
    echo -e "${LIGHTBLUE}3) Kill all Python Processes ${NC}"
    echo -e "${YELLOW}4) Launch MyTech ${NC}"
    echo -e "${PURPLE}5) Display Color Palette${NC}"
    echo -e "${GREEN}6) Grant terminal access to iCloud Drive${NC} "
    echo -e "${YELLOW}7) Restart Postgres 14${NC}"
    echo -e "${GREEN}8) OPEN MENU ${NC}"
    echo -e "${ORANGE}9) OPEN MENU ${NC}"
    echo -e "${RED_U}10) Create/replace .jbi symbolic links${NC}"
    echo -e "${RED_U}101) Generate an Encryption Key${NC}"
    echo -e "${RED_U}1977) Deinitialize vscode${NC}"
    echo -e "${RED_U}2008) DISCARD all changes and REPLACE with latest version from Azure Devops${NC}\n"

}

commit_current_folder() {

    echo "Comitting changes to current repository at: $pwd"
    git pull origin main
    git add .
    git commit -m "default commit message"
    git push origin main

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Commit Successful for ${PWD} ${NC}"
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
        sublime "${JBI_PATH}/jbi.sublime-workspace"
        ;;

    0)
        echo "You chose Option 0"
        commit_current_folder
        ;;

    1)
        echo "You chose Option 1: Commit and Push MyTech and .jbi \n"
        cd "${HOME}/.jbi" || {
            echo "Error: '${HOME}/.jbi' directory not found."
            exit 1
        }
        commit_current_folder

        cd "${HOME}/code/mytech" || {
            echo "Error: '${HOME}/code/mytech' directory not found."
            exit 1
        }
        commit_current_folder

        cd "${HOME}"

        echo "Commit and Push of MyTech and .jbi complete"

        exit 0

        ;;

    2)
        echo "You chose Option 2: Start ListGen"
        cd ~/code/mytech/docker/ListGen
        docker-compose up --build
        #     echo "Returning to menu."
        # fi
        exit 0
        ;;

    3)
        # Get a list of all Python processes and kill them
        echo -e "Killing all Python processes..."
        pkill -f python

        # Check if there are any remaining Python processes
        if pgrep -f python >/dev/null; then
            echo "Some Python processes could not be terminated."
        else
            echo "All Python processes have been successfully terminated."
        fi

        ;;

    4)
        echo "Start Product-Tools (Development Folder Port: 85)"
        source "$HOME/code/communify/communify_venv/bin/activate" && streamlit run "$HOME/code/communify/000_Communify_Home.py"
        ;;
    5)

        echo "Examples of Font Colors in Bash"
        echo -e "${BLACK}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${RED}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${RED_U}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${RED_BLINK}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${GREEN}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${GREEN_BLINK}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${YELLOW}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${PURPLE}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${PURPLE_U}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${PURPLE_BLINK}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${PINK}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${PINK_U}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${PINK_BLINK}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        echo -e "${LIGHTBLUE}The Quick Brown Fox Jumped Over the Lazy Dog ${NC}"
        exit 0

        ;;
    6)
        echo -e "${LIGHTBLUE} Grant Terminal access to iCloud Drive${NC}"
        echo -e "import os \nprint(os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs')) " >${HOME}/Library/Mobile\ Documents/com~apple~CloudDocs/terminal_access.py
        cd ${HOME}/Library/Mobile\ Documents/com~apple~CloudDocs
        python3 ${HOME}/Library/Mobile\ Documents/com~apple~CloudDocs/terminal_access.py
        echo -e "${GREEN}You should now have access to iCloud Drive in the terminal${NC}"
        exit 0

        ;;
    7)
        echo "Restarting Postgres 14"
        brew services restart postgresql@14
        echo "Postgres 14 restarted"
        exit 0
        ;;
    8)
        echo "Start / Restart LLMs and Chat Apps"
        cd ${COMMUNIFY_FOLDER_PATH} && llm_launch.sh
        exit 0
        ;;

    9)
        echo "Shut Down LLMs and Chat Apps"
        cd ${COMMUNIFY_FOLDER_PATH} && llm_launch.sh stop
        exit 0
        ;;

    10)

        PROJECT_NAME="product-development" # The name of your Azure DevOps project
        REPO_NAME=$(basename "$(pwd)")
        cp "${HOME}/code/.gitignore" "${PWD}/.gitignore"                                      # The name of your repository - this script sets it to the name of the current directory
        az repos create --name "$REPO_NAME" --project "$PROJECT_NAME"                         # Create a new repository in Azure DevOps
        git init                                                                              # Initialize a new Git repository in the current directory if it's not already a repository
        git add .                                                                             # Add all files in the current directory to the repository
        git commit -m "Initial commit"                                                        # Commit the files
        git remote add origin https://dev.azure.com/justbuildit/$PROJECT_NAME/_git/$REPO_NAME # Add the Azure DevOps repository as a remote to your local repository
        git push -u origin --all                                                              # Push your code to the Azure DevOps repository
        echo "Repository '$REPO_NAME' initialized and pushed to Azure DevOps."
        exit 0
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
            exit 0
        fi
        ;;

    2008)
        echo -e "${RED_U}#### WARNING ####"
        echo -e "${RED_BLINK}#### WARNING ####\n${NC}"
        echo -e "You are about to DESTROY all changes and"
        echo -e "replace them with the latest version in:"
        echo -e "$pwd\n"
        echo -e "#### THIS CANNOT BE UNDONE ####"
        if confirm "Do you want to proceed?"; then
            echo "Discarding all changes and replacing with latest version from Azure Devops"
            # git checkout -- .
            # git reset --hard
            # git fetch origin
            # git reset --hard origin/main
        else
            echo "Returning to menu."
        fi
        exit 0
        ;;
    2009)
        echo "You chose Option 2009:"
        ls -l
        cd "${PWD}"
        echo "is it different?"
        ls -l

        exit 0
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
        read -p "$1 ( ${PURPLE}Yy or ${PINK_U}Nn ${NC}): " yn
        case $yn in
        [Yy]*) return 0 ;;                                                     # User responded yes
        [Nn]*) return 1 ;;                                                     # User responded no
        *) echo "${RED_BLINK}Please answer Y for 'yes' or N for 'no'.${NC}" ;; # Invalid response
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
