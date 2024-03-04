#!bin/bash
#clear
echo "This script is designed to be run on a new Mac to set up the environment business and development use."
echo "Each step is laid out below:"

show_menu() {
    echo -e "Part 1: Install Homebrew Python 3 and Git\n"
    echo -e "Part 2: Install Azure CLI\n"
    echo -e "Part 3: Install environment variables using the code-admin scripts\n"
    echo -e "Part 4: Install Business Applications\n"
    echo -e "Part 5: Install Development Applications\n"
}

# Function to read the user's choice
read_choice() {
    local choice
    read -p "Enter next step: " choice
    case $choice in

    0)
        option0() {
            echo "You chose Option 0:"
            echo "This will copy the script to /usr/local/bin and add it to the PATH variable."

            cd ~

            # Get the path of the currently running script
            script_path=$0
            echo "script_path is: $script_path"

            hid_folder=".jbi"
            echo "hid_folder is: $hid_folder"

            echo "Going to make the .jbi folder"
            mkdir $hid_folder

            # Copy the script to the new location
            cp $script_path "$hid_folder/"

            new_location="$HOME/$hid_folder"
            touch .zshrc

            # Add the new location to the PATH variable
            echo "export PATH=\$PATH:$new_location" >>~/.zshrc

            source ~/.zshrc

            echo "JBI Setup copied and PATH updated."

        }
        if [ -z "$JBI_MAC_SETUP_PATH" ]; then
            option0
        else
            echo "The variable has a value: $my_variable"
        fi

        ;;

    1)
        option1() {
            echo "You chose Option 1:"
            echo "This will install: Homebrew, Python, Git" #, mkcert, nss"

            # Homebrew Installation
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

            # Add Homebrew to your PATH in /Users/yourname/.zprofile:
            (
                echo
                echo 'eval "$(/opt/homebrew/bin/brew shellenv)"'
            ) >>${HOME}/.zprofile
                 eval "$(/opt/homebrew/bin/brew shellenv)"
            source ${HOME}/.zprofile

            # Install Python 3
            brew install python3

            #Install Git
            brew install git

            #Create the the dmg folder
            mkdir -p ~/dmg/

            #Create the the code folder
            mkdir -p ~/code/

        }
        option1
        ;;

    2)
        option2() {

            #Ask the user how big to make the data dmg, but suggest 200GB.
            hdiutil create -size 300g -fs APFS -volname "data" -encryption AES-256 -stdinpass -attach ~/dmg/code.dmg
            #Use homebrew to install mkcert:
            # brew install mkcert
            # brew install nss
        }
        option2
        ;;
    3)
        option3() {
            echo "You chose Option 3:"
            echo "This will install Azure CLI and Dashlane CLI"

            #Install Rosetta
            softwareupdate --install-rosetta

            # brew install azure-cli
            # az login
            # az extension add --name azure-devops
            # az devops configure --defaults organization=https://dev.azure.com/outercircles

            #Dashlane CLI
            brew install dashlane/tap/dashlane-cli

            mkdir -p ~/code
            # git clone https://dev.azure.com/outercirclesdev/vscode-dev/_git/VSCodeVersions

        }
        option3
        ;;
    4)
        option4() {
            echp "You chose Option 3:"
            echo "This will install environment variables using the code-admin scripts."
            echo "This will also add the code-admin scripts to your PATH"

            JBI_FOLDER_PATH = "$HOME/.jbi"

            echo "source $JBI_FOLDER_PATH/ENV_VARIABLES.sh" >>~/.zshrc
            echo "source $JBI_FOLDER_PATH/ENV_VARIABLES.sh" >>~/.bashrc
        }
        option4
        ;;
    5)
        option5() {
            echo "You chose Option 4:"
            echo "This will install Business Applications"

            #Business Apps
            brew install --cask microsoft-office
            brew install --cask microsoft-teams
            brew install --cask dropbox

            #Browsers
            brew install --cask microsoft-edge
            brew install --cask google-chrome
            brew install --cask firefox
            brew install --cask arc

            #Design
            brew install --cask figma
            brew install --cask adobe-creative-cloud

            #Communication Apps
            brew install --cask slack
            brew install --cask zoom
            brew install --cask signal
            brew install --cask whatsapp

            #Music
            brew install --cask spotify

            #Local LLM Tools
            brew install --cask lm-studio

            #Security
            brew install 1password-cli

        }
        option5
        ;;

    6)
        option6() {
            #Xcode Command Line Tools
            xcode-select --install

            #Install Docker
            brew install docker

            #Install Node.js
            brew install node
            # verify installs:
            # node -v
            # npm -v

            #Install Visual Studio
            brew install --cask visual-studio-code

            #jq is a lightweight command-line JSON processor used in shell scripts. (used for ChatGPT)
            brew install jq

            #PDF Tools (for python)
            brew install poppler

            #Install Postgres and pgadmin4
            brew install postgresql
            brew services start postgresql
            # brew services stop postgresql #(if needed)
            brew install --cask pgadmin4

            #Development
            brew install jupyterlab
            python3 -m ipykernel install --user
            brew install --cask db-browser-for-sqlite
            brew install --cask dbeaver-community
            brew install --cask sublime-text
            brew install --cask postman
            #Audio Recording
            brew install portaudio
            brew install ffmpeg

            #Install LLama CPP
            brew install cmake
            cd /Applications
            git clone https://github.com/ggerganov/llama.cpp
            cd llama.cpp
            mkdir -p build && cd build
            cmake --build . --config Release

            brew install ollama

            brew install utm
        }
        option6
        ;;

    *)
        echo "Exiting ..."
        exit 0
        ;;
    esac

}

# Main logic loop
while true; do
    show_menu
    read_choice
done
