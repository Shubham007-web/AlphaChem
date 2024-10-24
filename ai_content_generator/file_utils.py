# file_utils.py file for ai_content_generator module

import os
import re

def sanitize_filename(filename):
    """
    Sanitizes a filename by replacing invalid characters that are not allowed in file paths.

    Parameters:
    - filename (str): The original filename.

    Returns:
    - str: The sanitized filename.
    """
    return re.sub(r'[\\/*?:"<>|]', "_", filename)

def create_folder_if_not_exists(path):
    """
    Creates the folder if it does not already exist.

    Parameters:
    - path (str): The directory path to check or create.

    Returns:
    - None
    """
    sanitized_path = sanitize_filename(path)
    if not os.path.exists(sanitized_path):
        os.makedirs(sanitized_path)
        print(f"Folder created: {sanitized_path}")
    else:
        print(f"Folder already exists: {sanitized_path}")

def find_next_version_file_name(file_path, base_file_name):
    """
    Finds the next available versioned file name in the given directory.
    If a file already exists, it appends a version number (e.g., V1, V2) to the filename.

    Parameters:
    - file_path (str): The directory where the file will be saved.
    - base_file_name (str): The base filename without extension.

    Returns:
    - str: The next available file name with a version number if needed.
    """
    version = 1
    base_file_name = sanitize_filename(base_file_name)
    file_name = f"{base_file_name}.docx"
    
    # Loop to check for existing files and find the next available version
    while os.path.exists(os.path.join(file_path, file_name)):
        version += 1
        file_name = f"V{version}_{base_file_name}.docx"
    
    return file_name
