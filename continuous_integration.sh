#!/bin/bash

# Set the base directory for your projects
base_dir="${HOME}/code"

# Navigate to the base directory
cd "$base_dir" || {
  echo "Error: Directory '$base_dir' not found."
  exit 1
}

# Get the list of repositories using Azure CLI with -o tsv for easier parsing
repo_info=$(az repos list --project product-development --org https://dev.azure.com/justbuildit --query "[].{Name:name, HTTPS:remoteUrl}" -o tsv)

# Check if repo_info is empty
if [ -z "$repo_info" ]; then
  echo "No repositories found or error retrieving repositories."
  exit 1
fi

# Iterate through the repo info
while IFS=$'\t' read -r repo_name repo_url; do
  if [ -d "$repo_name" ]; then
    # Existing repo: cd into it and pull
    cd "$repo_name"
    echo "Updating existing repository: $repo_name"
    git pull origin main || echo "Error: Pull failed for $repo_name"
    cd .. # Go back to the base directory
  else
    # New repo: clone it
    echo "Cloning new repository: $repo_name"
    git clone $repo_url
  fi
done <<<"$repo_info"
