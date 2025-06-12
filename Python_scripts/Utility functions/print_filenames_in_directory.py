import os

def print_filenames_in_directory(directory_path):
    """
    Prints all file names in the given directory.

    Parameters:
    - directory_path (str): Path to the directory
    """
    if not os.path.isdir(directory_path):
        print(f"❌ The path '{directory_path}' is not a valid directory.")
        return

    files = os.listdir(directory_path)
    for f in files:
        full_path = os.path.join(directory_path, f)
        if os.path.isfile(full_path):
            print(f)
