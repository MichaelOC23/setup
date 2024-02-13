#!/bin/bash

#promt the user for the name of the venv
echo "Enter the name of the virtual environment: "
read venvname
python3 -m venv /Volumes/code/vscode/virtual-environments/$venvname --upgrade-deps --prompt $venvname
source /Volumes/code/vscode/virtual-environments/$venvname/bin/activate
