#!/bin/bash


#Key folders
CODE_FOLDER_PATH="${HOME}/code"

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

echo "You chose Option 1: Commit and Push All: VSCODE .JBI COMMUNIFY\n"
echo "Committing and pushing $VSCODE_FOLDER_PATH"
# Navigate to ~/vsce
cd "$CODE_FOLDER_PATH/communify" || exit
commit_current_folder

cd "$CODE_FOLDER_PATH/product-tools" || exit
commit_current_folder

cd "$CODE_FOLDER_PATH/vscode" || exit
commit_current_folder

cd "$CODE_FOLDER_PATH/code_admin" || exit
commit_current_folder

cd $HOME/.jbi || exit
commit_current_folder

