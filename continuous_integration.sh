#!/bin/bash

# Set the base directory for your projects
base_dir="${HOME}/code"

# Navigate to the base directory
cd "$base_dir" || { echo "Error: Directory '$base_dir' not found."; exit 1; }

# Get the list of repositories using Azure CLI
repo_info=$(az repos list --project product-development --org https://dev.azure.com/justbuildit --query "[].{Name:name, HTTPS:remoteUrl}" -o table)

# Iterate through the repo info 
while IFS= read -r line; do
  # Skip header lines
  if [[ $line == *"Name"* || $line == *"-"* ]]; then 
      continue
  fi

  repo_name=$(echo "$line" | awk '{print $1}')
  repo_url=$(echo "$line" | awk '{print $2}')

  if [ -d "$repo_name" ]; then
    # Existing repo: cd into it and pull
    cd "$repo_name"
    echo "Updating existing repository: $repo_name"
    git pull origin main || echo "Error: Pull failed for $repo_name"
    cd ..  # Go back to the base directory
  else
    # New repo: clone it 
    echo "Cloning new repository: $repo_name"
    git clone $repo_url 
  fi
done <<< "$repo_info"
