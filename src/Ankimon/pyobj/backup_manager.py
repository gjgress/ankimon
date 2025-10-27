
import base64
import json
import os
import shutil
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from aqt import mw
from aqt.utils import showInfo, showWarning, askUser

from ..utils import close_anki
from ..resources import user_path, addon_dir

class BackupManager:
    """A robust and feature-rich system for managing Ankimon user data backups.

    This class is a critical component of the addon's data management strategy,
    providing users with the ability to create, restore, and delete backups,
    as well as an automated backup system that runs when Anki is closed. This
    is essential for protecting users from data loss and for providing a
    seamless recovery process in the event of data corruption.
    """

    _OBFUSCATION_KEY = "H0tP-!s-N0t-4-C@tG!rL_v2"
    FILES_TO_BACKUP = [
        "mypokemon.json",
        "mainpokemon.json",
        "badges.json",
        "items.json",
        "teams.json",
        "data.json",
        "todays_shop.json",
        "config.obf",
    ]
    MAX_BACKUPS = 5
    MAX_BACKUP_AGE_DAYS = 14

    def __init__(self, logger, settings_obj):
        """Initializes the BackupManager.

        Args:
            logger: An instance of the logger class for recording events.
            settings_obj: An instance of the `Settings` class for accessing
                          user preferences.
        """
        self.logger = logger
        self.settings_obj = settings_obj
        self.user_files_path = user_path
        self.addon_path = addon_dir
        self.backups_path = self.addon_path.parent / "ankimon_backups"
        self.backups_path.mkdir(exist_ok=True)

    def _deobfuscate_data(self, obfuscated_str: str) -> Optional[Dict[str, Any]]:
        """De-obfuscates the user's configuration data.

        This method is used to read the obfuscated configuration file, which
        contains sensitive user data such as the trainer's name and cash.

        Args:
            obfuscated_str (str): The obfuscated string to be de-obfuscated.

        Returns:
            dict: The de-obfuscated data as a dictionary, or None if an error
                  occurs.
        """
        try:
            new_separator = "---DATA_START---"
            old_separator = "\n---"
            
            if new_separator in obfuscated_str:
                parts = obfuscated_str.split(new_separator)
                obfuscated_data = parts[1]
            elif old_separator in obfuscated_str:
                parts = obfuscated_str.split(old_separator)
                obfuscated_data = parts[1]
            else:
                obfuscated_data = obfuscated_str

            obfuscated_bytes = base64.b64decode(obfuscated_data)
            deobfuscated_bytes = bytearray()
            key_bytes = self._OBFUSCATION_KEY.encode('utf-8')
            for i, byte in enumerate(obfuscated_bytes):
                deobfuscated_bytes.append(byte ^ key_bytes[i % len(key_bytes)])
            return json.loads(deobfuscated_bytes.decode('utf-8'))
        except Exception as e:
            self.logger.log("error", f"Failed to deobfuscate data: {e}")
            return None

    def get_backups(self) -> List[Dict[str, Any]]:
        """Retrieves a list of all available backups.

        This method scans the backup directory and reads the summary data for
        each backup, providing a comprehensive overview of the available
        restore points.

        Returns:
            list: A list of dictionaries, where each dictionary represents a
                  backup and contains its summary data.
        """
        backups = []
        for backup_dir in sorted(self.backups_path.iterdir(), reverse=True):
            if backup_dir.is_dir():
                summary_path = backup_dir / "summary.json"
                if summary_path.exists():
                    with open(summary_path, 'r', encoding='utf-8') as f:
                        try:
                            summary = json.load(f)
                            summary['path'] = str(backup_dir)
                            backups.append(summary)
                        except json.JSONDecodeError:
                            self.logger.log("error", f"Could not read summary for backup: {backup_dir.name}")
        return backups

    def create_backup(self, manual=False):
        """Creates a new backup of the user's data.

        This method can be triggered manually by the user or automatically when
        Anki is closed. It copies all of the user's data files to a new
        timestamped directory and generates a summary of the backup.

        Args:
            manual (bool, optional): Whether the backup was initiated
                                     manually by the user.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        backup_dir = self.backups_path / f"backup_{timestamp}"
        
        try:
            backup_dir.mkdir()
            
            for filename in self.FILES_TO_BACKUP:
                source_path = self.user_files_path / filename
                if source_path.exists():
                    shutil.copy2(source_path, backup_dir / filename)

            summary = self._generate_summary(backup_dir)
            summary['manual'] = manual
            with open(backup_dir / "summary.json", 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=4)
            
            if manual:
                showInfo("Manual backup created successfully.")
            self.logger.log("info", f"Created backup: {backup_dir.name}")

        except Exception as e:
            self.logger.log("error", f"Failed to create backup: {e}")
            if manual:
                showWarning(f"Failed to create backup: {e}")
        
        self.cleanup_backups()

    def _generate_summary(self, backup_dir: Path) -> Dict[str, Any]:
        """Generates a summary of a backup's contents.

        This method reads the key data files from a backup and extracts
        important information, such as the trainer's name, level, and the
        number of Pokémon and items. This summary is then displayed to the user
        in the backup manager, helping them to identify the correct backup to
        restore.

        Args:
            backup_dir (Path): The path to the backup directory.

        Returns:
            dict: A dictionary containing the summary data.
        """
        summary = {
            "date": backup_dir.name.replace("backup_", "").replace("_", " "),
            "main_pokemon_name": "N/A",
            "main_pokemon_level": "N/A",
            "pokemon_count": 0,
            "trainer_name": "N/A",
            "trainer_cash": 0,
            "trainer_level": 0,
            "item_count": 0,
        }

        # Read mainpokemon.json for main Pokémon info
        mainpokemon_path = backup_dir / "mainpokemon.json"
        if mainpokemon_path.exists():
            with open(mainpokemon_path, 'r', encoding='utf-8') as f:
                try:
                    mainpokemon_data = json.load(f)
                    if mainpokemon_data:
                        summary["main_pokemon_name"] = mainpokemon_data[0].get("name", "N/A")
                        summary["main_pokemon_level"] = mainpokemon_data[0].get("level", "N/A")
                except (json.JSONDecodeError, IndexError):
                    pass

        # Read mypokemon.json for total Pokémon count
        mypokemon_path = backup_dir / "mypokemon.json"
        if mypokemon_path.exists():
            with open(mypokemon_path, 'r', encoding='utf-8') as f:
                try:
                    mypokemon_data = json.load(f)
                    summary["pokemon_count"] = len(mypokemon_data)
                except json.JSONDecodeError:
                    pass

        # Read items.json for total item count
        items_path = backup_dir / "items.json"
        if items_path.exists():
            with open(items_path, 'r', encoding='utf-8') as f:
                try:
                    items_data = json.load(f)
                    summary["item_count"] = sum(item.get('quantity', 0) for item in items_data)
                except json.JSONDecodeError:
                    pass

        # Read config.obf for trainer info
        config_path = backup_dir / "config.obf"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                obfuscated_data = f.read()
            config_data = self._deobfuscate_data(obfuscated_data)
            if config_data:
                summary["trainer_name"] = config_data.get("trainer.name", "N/A")
                summary["trainer_cash"] = config_data.get("trainer.cash", 0)
                summary["trainer_level"] = config_data.get("trainer.level", 1)
        
        return summary

    def restore_backup(self, backup_path_str: str):
        """Restores the user's data from a selected backup.

        This method overwrites the current user data with the data from the
        selected backup. It then closes Anki to ensure that the changes are
        applied correctly.

        Args:
            backup_path_str (str): The path to the backup to be restored.
        """
        backup_path = Path(backup_path_str)
        if not backup_path.is_dir():
            showWarning("Selected backup path does not exist.")
            return

        if not askUser(
            "Are you sure you want to restore this backup? This will overwrite your current Ankimon data. Anki will be closed to apply the changes."
        ):
            return

        try:
            for filename in self.FILES_TO_BACKUP:
                backup_file = backup_path / filename
                if backup_file.exists():
                    shutil.copy2(backup_file, self.user_files_path / filename)
                else:
                    # If a file doesn't exist in backup, it should be removed from user_files
                    user_file = self.user_files_path / filename
                    if user_file.exists():
                        os.remove(user_file)

            showInfo("Backup restored successfully. Anki will now close. Please restart Anki to see the changes.")
            close_anki()

        except Exception as e:
            self.logger.log("error", f"Failed to restore backup: {e}")
            showWarning(f"Failed to restore backup: {e}")

    def delete_backup(self, backup_path_str: str):
        """Deletes a selected backup.

        Args:
            backup_path_str (str): The path to the backup to be deleted.
        """
        backup_path = Path(backup_path_str)
        if not backup_path.is_dir():
            showWarning("Selected backup path does not exist.")
            return
        try:
            shutil.rmtree(backup_path)
            self.logger.log("info", f"Deleted backup: {backup_path.name}")
            showInfo("Backup deleted successfully.")
        except Exception as e:
            self.logger.log("error", f"Failed to delete backup: {e}")
            showWarning(f"Failed to delete backup: {e}")

    def cleanup_backups(self):
        """Deletes old backups based on the defined retention policy.

        This method is called after a new backup is created. It deletes
        backups that are older than the maximum age and, if necessary, deletes
        the oldest backups to ensure that the total number of backups does not
        exceed the maximum limit.
        """
        backups = sorted(self.backups_path.iterdir(), key=os.path.getmtime)
        
        # Delete backups older than MAX_BACKUP_AGE_DAYS
        for backup_dir in backups:
            backup_time = datetime.datetime.fromtimestamp(os.path.getmtime(backup_dir))
            if (datetime.datetime.now() - backup_time).days > self.MAX_BACKUP_AGE_DAYS:
                shutil.rmtree(backup_dir)
                self.logger.log("info", f"Deleted old backup: {backup_dir.name}")

        # Keep only the latest MAX_BACKUPS, unless in developer mode
        if not self.settings_obj.get("misc.developer_mode", False):
            backups = sorted(self.backups_path.iterdir(), key=os.path.getmtime)
            while len(backups) > self.MAX_BACKUPS:
                oldest_backup = backups.pop(0)
                shutil.rmtree(oldest_backup)
                self.logger.log("info", f"Deleted oldest backup to maintain max count: {oldest_backup.name}")

    def on_anki_close(self):
        """Creates a backup when Anki is closed.

        This method is connected to Anki's `profile_will_close` hook, ensuring
        that a backup is created every time the user closes their profile.
        """
        # This logic can be expanded with the developer mode setting
        self.create_backup(manual=False)
