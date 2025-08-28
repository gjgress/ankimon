import platform
import sys

import os
import json

# Define ADDON_ID globally for consistent use
ADDON_ID = "Ankimon" # Ensure this matches the actual addon ID Ankimon uses with addonManager

class Settings: # This class will serve as the config object for both real and mock environments
    def __init__(self):
        self._config = {}
        loaded_config = {}
        
        # Try to load real config from Anki's addonManager
        try:
            from aqt import mw
            if hasattr(mw, 'addonManager') and mw.addonManager:
                loaded_config = mw.addonManager.getConfig(ADDON_ID)
                if loaded_config:
                    print(f"Settings: Loaded config from Anki's addonManager for {ADDON_ID}.")
                else:
                    print(f"Settings: Addon config was empty from Anki's addonManager, using defaults for {ADDON_ID}.")
            else:
                print("Settings: aqt.mw or addonManager not fully available, using hardcoded defaults.")
        except ImportError:
            # This is expected in the test environment before mocks are fully set up.
            print("Settings: aqt not available (test environment or no Anki), using hardcoded defaults.")
        except Exception as e:
            print(f"Settings: Error loading config from Anki's addonManager: {e}, using defaults.")

        # Define comprehensive default values, mirroring src\Ankimon\config.json
        # This block needs to be accessible always, regardless of Anki/aqt availability.
        default_config = {
            "battle.dmg_in_reviewer": True,
            "battle.automatic_battle": 0,
            "battle.cards_per_round": 2,
            "battle.daily_average": 100,
            "battle.card_max_time": 60,
            "controls.pokemon_buttons": True,
            "controls.defeat_key": "5",
            "controls.catch_key": "6",
            "controls.key_for_opening_closing_ankimon": "Ctrl+N",
            "controls.allow_to_choose_moves": False,
            "gui.animate_time": True,
            "gui.gif_in_collection": True,
            "gui.styling_in_reviewer": True,
            "gui.hp_bar_config": True,
            "gui.pop_up_dialog_message_on_defeat": False,
            "gui.review_hp_bar_thickness": 2,
            "gui.reviewer_image_gif": False,
            "gui.reviewer_text_message_box": True,
            "gui.reviewer_text_message_box_time": 3,
            "gui.show_mainpkmn_in_reviewer": 1,
            "gui.view_main_front": True,
            "gui.xp_bar_config": True,
            "gui.xp_bar_location": 2,
            "audio.sound_effects": False,
            "audio.sounds": True,
            "audio.battle_sounds": False,
            "misc.gen1": True,
            "misc.gen2": True,
            "misc.gen3": True,
            "misc.gen4": True,
            "misc.gen5": True,
            "misc.gen6": True,
            "misc.gen7": False,
            "misc.gen8": False,
            "misc.gen9": False,
            "misc.remove_level_cap": False,
            "misc.leaderboard": False,
            "misc.language": 9,
            "misc.ssh": True,
            "misc.YouShallNotPass_Ankimon_News": False,
            "misc.discord_rich_presence": False,
            "misc.discord_rich_presence_text": 1,
            "misc.show_tip_on_startup": True,
            "misc.last_tip_index": 0,
            "trainer.name": "Ash",
            "trainer.sprite": "ash",
            "trainer.id": 0,
            "trainer.cash": 0
        }

        # Merge loaded config with defaults, loaded config takes precedence
        self._config.update(default_config)
        self._config.update(loaded_config) # Overwrite defaults with actual loaded values
        
    def get(self, key, default=None):
        return self._config.get(key, default)

# Instantiate the Settings class to be the global config object for this module
config = Settings()

# Now, use the 'config' object (either real or mocked) to get values.
# The config object is now ready for use by the rest of the file.

# Accessing config values, ensuring they are available or have defaults
pop_up_dialog_message_on_defeat = config.get("gui.pop_up_dialog_message_on_defeat", True)
reviewer_text_message_box = config.get("gui.reviewer_text_message_box", True)
reviewer_text_message_box_time = config.get("gui.reviewer_text_message_box_time", 5000) # 5 seconds in ms
reviewer_text_message_box_time = reviewer_text_message_box_time * 1000 #times 1000 for s => ms
reviewer_image_gif = config.get("gui.reviewer_image_gif", True)
show_mainpkmn_in_reviewer = config.get("gui.show_mainpkmn_in_reviewer", 1) #0 is off, 1 normal, 2 battle mode
xp_bar_config = config.get("gui.xp_bar_config", True)
review_hp_bar_thickness = config.get("gui.review_hp_bar_thickness", 3) #2 = 8px, 3# 12px, 4# 16px, 5# 20px
hp_bar_config = config.get("gui.hp_bar_config", 3) #2 = 8px, 3# 12px, 4# 16px, 5# 20px
xp_bar_location = config.get("gui.xp_bar_location", 2) #1 top, 2 = bottom
animate_time = config.get("gui.animate_time", True) #default: true; false = animate for 0.8 seconds
view_main_front = config.get("gui.view_main_front", True) #default: true => -1; false = 1
gif_in_collection = config.get("gui.gif_in_collection", True) #default: true => -1; false = 1
styling_in_reviewer = config.get("gui.styling_in_reviewer", True) #default: true; false = no styling in reviewer

automatic_battle = config.get("battle.automatic_battle", 0) #default: 0; 1 = catch_pokemon; 2 = defeat_pokemon
dmg_in_reviewer = config.get("battle.dmg_in_reviewer", False) #default: false; true = mainpokemon is getting damaged in reviewer for false answers
cards_per_round = config.get("battle.cards_per_round", 5)

leaderboard = config.get("misc.leaderboard", False)  # Default to False if not found
ankiweb_sync = config.get("misc.ankiweb_sync", False)  # Default to False if not found
no_more_news = config.get("misc.YouShallNotPass_Ankimon_News", False) #default: false; true = no more news
remove_levelcap = config.get("misc.remove_level_cap", False) #default: false; true = no more news
ssh = config.get("misc.ssh", True) #for eduroam users - false ; default: true
language = config.get("misc.language", 9)

ankimon_key = config.get("controls.key_for_opening_closing_ankimon", "Ctrl+Shift+A")
defeat_shortcut = config.get("controls.defeat_key", 5) #default: 5; ; Else if not 5 => controll + Key for capture
catch_shortcut = config.get("controls.catch_key", 6) #default: 6; Else if not 6 => controll + Key for capture
reviewer_buttons = config.get("controls.pokemon_buttons", True) #default: true; false = no pokemon buttons in reviewer

sound_effects = config.get("audio.sound_effects", False) #default: false; true = sound_effects on
sounds = config.get("audio.sounds", [])
battle_sounds = config.get("audio.battle_sounds", [])


# Get the system name (e.g., 'Windows', 'Linux', 'Darwin')
system_name = platform.system()

# Determine system category
if system_name == "Windows" or system_name == "Linux":
    # Assign 'win_lin' for Windows or Linux
    system = "win_lin"
elif system_name == "Darwin":
    # Assign 'mac' for macOS
    system = "mac"
else:
    # Default or fallback for unknown systems
    system = "unknown"

if sound_effects is True:
    # This import should ideally be handled where 'playsound' is actually used,
    # or ensure it's available in the test environment if needed here.
    # For now, we'll keep it as is, assuming it might be imported later.
    try:
        from . import playsound
    except ImportError:
        print("Warning: 'playsound' module not found, but sound_effects is enabled.")
        # Handle the case where playsound is not available in the test env if necessary
        pass
