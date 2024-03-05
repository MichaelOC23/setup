#!/bin/bash

# Navigate to the code directory
cd ${HOME}/code

# Iterate over each subdirectory and pull git updates
for d in */; do
    echo "Updating repository in $d"
    cd "${HOME}/code/$d"
    git pull
    cd ..
done
