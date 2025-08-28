import platform
import sys

# Attempt to import mw from aqt, but provide a fallback for the test environment
try:
    from aqt import mw
    # If mw is available, it means we are running in a real Anki environment.
    # We can then try to get the config.
    config = mw.addonManager.getConfig(__name__)
except ImportError:
    # If aqt is not available, we are likely in the test environment.
    # In this case, we need to mock the config.
    # We'll use a mock Settings object that can provide default values.
import aqt # Required to access aqt.mw.addonManager
import os
import json

ADDON_ID = "Ankimon" # Assuming Ankimon's addon ID, ensure this matches actual addon ID

print("Running in test environment, mocking config.")
class MockSettings:
        def __init__(self):
            self._config = {}
            # Try to load config from the mock addon manager
            loaded_config = {}
            if hasattr(aqt, 'mw') and hasattr(aqt.mw, 'addonManager') and aqt.mw.addonManager:
                try:
                    loaded_config = aqt.mw.addonManager.getConfig(ADDON_ID)
                    if loaded_config:
                        print(f"MockSettings: Loaded config from mock addonManager for {ADDON_ID}.")
                    else:
                        print("MockSettings: Addon config was empty from mock addonManager, using defaults.")
                except Exception as e:
                    print(f"MockSettings: Error loading config from mock addonManager: {e}, using defaults.")
            else:
                print("MockSettings: aqt.mw or addonManager not available, using hardcoded defaults.")

            # Define comprehensive default values, mirroring src\Ankimon\config.json
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
            # Return the value from our mock config, or the default if not found
            return self._config.get(key, default)

    # Instantiate the mock settings to get config values
    settings_instance = MockSettings()
    config = settings_instance # Use the mock settings instance as our config object

# Now, use the 'config' object (either real or mocked) to get values.
# We need to ensure that if 'config' is a mock object, it behaves like a dictionary
# or has a .get() method. The MockSettings class above provides this.

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
