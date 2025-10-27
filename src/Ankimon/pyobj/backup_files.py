import os
import shutil
from datetime import datetime
import json
from aqt.utils import showInfo
from aqt import mw
from ..resources import mypokemon_path, mainpokemon_path, itembag_path, badgebag_path, user_path_credentials, backup_root
# Define backup directory and files to back up
backup_folders = [os.path.join(backup_root, f"backup_{i}") for i in range(1, 4)]
files_to_backup = [mypokemon_path, mainpokemon_path, itembag_path, badgebag_path, user_path_credentials]  # Adjust as needed

def create_backup_folder(folder_path):
    """Creates a new backup folder and copies the user's data into it.

    This function also writes a timestamp file within the backup folder,
    which is used to determine the age of the backup for rotation purposes.

    Args:
        folder_path (str): The path where the new backup folder will be created.
    """
    os.makedirs(folder_path, exist_ok=True)

    # Create a timestamp file
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(folder_path, "backup_info.txt"), "w") as f:
        f.write(f"Backup created on: {timestamp}")

    # Copy the files into the new backup folder
    for file in files_to_backup:
        if os.path.exists(file):
            shutil.copy(file, folder_path)

def rotate_backups():
    """Manages a rolling backup system.

    This function implements a backup rotation strategy, where the oldest
    backup is deleted to make space for a new one. It ensures that a fixed
    number of recent backups are kept, preventing excessive disk usage.
    """
    if os.path.exists(backup_folders[-1]):
        shutil.rmtree(backup_folders[-1])  # Delete oldest backup

    # Shift backups (backup_2 → backup_3, backup_1 → backup_2)
    for i in range(len(backup_folders) - 1, 0, -1):
        if os.path.exists(backup_folders[i - 1]):
            shutil.move(backup_folders[i - 1], backup_folders[i])

def is_backup_needed():
    """Checks if a new backup is required based on a two-week interval.

    This function reads the timestamp from the most recent backup and
    determines if enough time has passed to warrant creating a new one.

    Returns:
        bool: True if a new backup is needed, False otherwise.
    """
    if not os.path.exists(backup_folders[0]):
        return True  # No backups exist, so we need one

    with open(os.path.join(backup_folders[0], "backup_info.txt"), "r") as f:
        date_str = f.readline().replace("Backup created on: ", "").strip()
        last_backup_date = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

    return (datetime.now() - last_backup_date).days >= 14  # Check if 2 weeks have passed

def run_backup():
    """Executes the full backup process.

    This is the main entry point for the backup system. It checks if a backup
    is needed, rotates the existing backups, and creates a new one as
    required.
    """
    if is_backup_needed():
        rotate_backups()
        create_backup_folder(backup_folders[0])
        mw.logger.log("game","New backup created successfully.")
    else:
        mw.logger.log("game","No backup needed yet.")
