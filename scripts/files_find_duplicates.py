import os
import hashlib
import filecmp

def get_folder_hash(folder_path):
    """Generate a hash for the contents of a folder."""
    hash_md5 = hashlib.md5()
    for root, _, files in os.walk(folder_path):
        for file in sorted(files):  # Sort to ensure consistent order
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'rb') as f:
                    while chunk := f.read(8192):
                        hash_md5.update(chunk)
            except (OSError, IOError):
                # Skip files that can't be read
                continue
    return hash_md5.hexdigest()

def find_duplicate_folders(root_dir):
    """Find and list duplicate folders based on their contents."""
    folder_hashes = {}
    duplicates = []

    for dirpath, dirnames, _ in os.walk(root_dir):
        for dirname in dirnames:
            folder_path = os.path.join(dirpath, dirname)
            folder_hash = get_folder_hash(folder_path)
            if folder_hash in folder_hashes:
                duplicates.append((folder_hashes[folder_hash], folder_path))
            else:
                folder_hashes[folder_hash] = folder_path

    return duplicates

root_dir = "/Volumes/4TBSandisk/"
duplicate_folders = find_duplicate_folders(root_dir)

if duplicate_folders:
    print("Duplicate folders found:")
    for original, duplicate in duplicate_folders:
        print(f"Original: {original}\nDuplicate: {duplicate}\n")
else:
    print("No duplicate folders found.")
