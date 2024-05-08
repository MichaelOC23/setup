#!/bin/bash

# Check for argument (target directory)
if [ -z "$1" ]; then
  echo "Usage: $0 <target_directory>"
  exit 1
fi

# Source directory (template)
template_dir="${HOME}/.jbi/repo_template"

# Check if source directory exists
if [ ! -d "$template_dir" ]; then
  echo "Error: Template directory '$template_dir' does not exist."
  exit 1
fi

# Target directory
target_dir="$1"

# Copy function with preserve permissions flag (-p)
copy_with_permissions() {
  local src="$1"
  local dst="$2"
  cp -rp "$src" "$dst"
}

# Copy entire directory structure
echo "Copying template to '$target_dir'..."
rsync -av --exclude=.git* "$template_dir/" "$target_dir/"

# Handle potential errors during copy
if [ $? -ne 0 ]; then
  echo "Error: An error occurred during copy process."
  exit 1
fi

echo "Template copied successfully!"

