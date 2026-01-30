from .imports import *

def ClearDirectory(target_dir):
    """
    Function: clear_directory
    What it does: Removes all files and subfolders in the specified directory.
    Parameters:
        target_dir (str): Path to the directory to be cleared.
    """
    if not os.path.exists(target_dir):
        print("The directory does not exist:", target_dir)
        return

    for item in os.listdir(target_dir):
        item_path = os.path.join(target_dir, item)
        try:
            if os.path.isfile(item_path) or os.path.islink(item_path):
                os.unlink(item_path)
                print("File removed:", item_path)
            elif os.path.isdir(item_path):
                shutil.rmtree(item_path)
                print("Folder removed:", item_path)
        except Exception as e:
            print("Failed to remove {}. Reason: {}".format(item_path, e))