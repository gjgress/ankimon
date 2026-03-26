# -*- coding: utf-8 -*-

# Ankimon
# Copyright (C) 2024 Unlucky-Life

# This program is free software: you can redistribute it and/or modify
# by the Free Software Foundation
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# Important - If you redistribute it and/or modify this addon - must give contribution in Title and Code
# aswell as ask for permission to modify / redistribute this addon or the code itself

try:
    from .debug_console import show_ankimon_dev_console
except ModuleNotFoundError:
    # Debug console should not be available to non devs, so it's fine if this import doesn't succeed
    pass

import json
import random
import copy
from typing import Union

import aqt
from anki.hooks import addHook, wrap
from aqt import gui_hooks, mw, utils
from aqt.qt import QDialog
from aqt.operations import QueryOp
from aqt.reviewer import Reviewer
from aqt.utils import downArrow, showWarning, tr, tooltip
from PyQt6.QtWidgets import QDialog
from aqt.gui_hooks import webview_will_set_content
from aqt.webview import WebContent
import markdown

from .resources import generate_startup_files, user_path, IS_EXPERIMENTAL_BUILD, addon_ver, addon_dir
generate_startup_files(addon_dir, user_path)

from .singletons import settings_obj
no_more_news = settings_obj.get("misc.YouShallNotPass_Ankimon_News")
ssh = settings_obj.get("misc.ssh")
defeat_shortcut = settings_obj.get("controls.defeat_key") #default: 5; ; Else if not 5 => controll + Key for capture
catch_shortcut = settings_obj.get("controls.catch_key") #default: 6; Else if not 6 => controll + Key for capture
reviewer_buttons = settings_obj.get("controls.pokemon_buttons") #default: true; false = no pokemon buttons in reviewer

from .resources import (
    addon_dir,
    pkmnimgfolder,
    mypokemon_path,
    itembag_path,
    sound_list_path,
)
from .menu_buttons import create_menu_actions
from .hooks import setupHooks
from .texts import _bottomHTML_template, button_style
from .utils import (
    check_folders_exist,
    safe_get_random_move,
    test_online_connectivity,
    read_local_file,
    read_github_file,
    compare_files,
    write_local_file,
    count_items_and_rewrite,
    play_effect_sound,
    get_main_pokemon_data,
    play_sound,
    load_collected_pokemon_ids,
)
from .functions.url_functions import open_team_builder, rate_addon_url, report_bug, join_discord_url, open_leaderboard_url
from .functions.badges_functions import get_achieved_badges, handle_review_count_achievement, check_for_badge, receive_badge
from .functions.pokemon_showdown_functions import export_to_pkmn_showdown, export_all_pkmn_showdown, flex_pokemon_collection
from .functions.drawing_utils import tooltipWithColour
from .functions.discord_function import DiscordPresence
from .functions.rate_addon_functions import rate_this_addon
from .functions.encounter_functions import (
    generate_random_pokemon,
    new_pokemon,
    catch_pokemon,
    kill_pokemon,
    handle_enemy_faint,
    handle_main_pokemon_faint
)
from .functions.battle_handler import on_review_card
from .gui_entities import UpdateNotificationWindow, CheckFiles
from .pyobj.download_sprites import show_agreement_and_download_dialog
from .pyobj.help_window import HelpWindow
from .pyobj.backup_files import run_backup
from .pyobj.backup_manager import BackupManager
from .pyobj.ankimon_sync import setup_ankimon_sync_hooks, check_and_sync_pokemon_data
from .pyobj.tip_of_the_day import show_tip_of_the_day
from .singletons import (
    reviewer_obj,
    logger,
    settings_obj,
    settings_window,
    translator,
    main_pokemon,
    enemy_pokemon,
    trainer_card,
    ankimon_tracker_obj,
    test_window,
    achievement_bag,
    data_handler_obj,
    data_handler_window,
    shop_manager,
    ankimon_tracker_window,
    pokedex_window,
    eff_chart,
    gen_id_chart,
    license,
    credits,
    evo_window,
    starter_window,
    item_window,
    version_dialog,
    achievements,
    pokemon_pc
)

from .pyobj.pokemon_trade import check_and_award_monthly_pokemon

from .pyobj.error_handler import show_warning_with_traceback

mw.settings_ankimon = settings_window
mw.logger = logger
mw.translator = translator
mw.settings_obj = settings_obj

from .gui_classes import overview_team

overview_team.init_hooks()

# Log an startup message
logger.log_and_showinfo('game', translator.translate("startup"))
logger.log_and_showinfo('game', translator.translate("backing_up_files"))

#backup_files
try:
    run_backup()
except Exception as e:
    show_warning_with_traceback(parent=mw, exception=e, message="Backup error:")

backup_manager = BackupManager(logger, settings_obj)

if settings_obj.get("misc.developer_mode"):
    backup_manager.create_backup(manual=False)

# Initialize collected IDs cache
# Call this during addon initialization
collected_pokemon_ids = set()
_collection_loaded = False
if not _collection_loaded: # If the collection hasn't already been loaded
    collected_pokemon_ids = load_collected_pokemon_ids()
    _collection_loaded = True



with open(sound_list_path, "r", encoding="utf-8") as json_file:
    sound_list = json.load(json_file)

ankimon_tracker_obj.pokemon_encouter = 0

"""
get web exports ready for special reviewer look
"""


# Set up web exports for static files
mw.addonManager.setWebExports(__name__, r"user_files/.*\.(css|js|jpg|gif|html|ttf|png|mp3)")

def on_webview_will_set_content(web_content: WebContent, context) -> None:
    if not isinstance(context, aqt.reviewer.Reviewer):
        return
    ankimon_package = mw.addonManager.addonFromModule(__name__)
    web_content.js.append(f"/_addons/{ankimon_package}/user_files/web/ankimon_hud_portal.js")



webview_will_set_content.append(on_webview_will_set_content)

# check for sprites, data
sound_files = check_folders_exist(pkmnimgfolder, "sounds")
back_sprites = check_folders_exist(pkmnimgfolder, "back_default")
back_default_gif = check_folders_exist(pkmnimgfolder, "back_default_gif")
front_sprites = check_folders_exist(pkmnimgfolder, "front_default")
front_default_gif = check_folders_exist(pkmnimgfolder, "front_default_gif")
item_sprites = check_folders_exist(pkmnimgfolder, "items")
badges_sprites = check_folders_exist(pkmnimgfolder, "badges")

database_complete = all([
        back_sprites, front_sprites, front_default_gif, back_default_gif, item_sprites, badges_sprites
])

if not database_complete:
    show_agreement_and_download_dialog(force_download=True)
    dialog = CheckFiles()
    dialog.show()

sync_dialog = None

#If reviewer showed question; start card_timer for answering card
def on_show_question(Card):
    """
    This function is called when a question is shown.
    You can access and manipulate the card object here.
    """
    ankimon_tracker_obj.start_card_timer()  # This line should have 4 spaces of indentation

def on_show_answer(Card):
    """
    This function is called when a question is shown.
    You can access and manipulate the card object here.
    """
    ankimon_tracker_obj.stop_card_timer()  # This line should have 4 spaces of indentation

def on_reviewer_did_show_question(card):
    reviewer_obj.update_life_bar(mw.reviewer, None, None)

gui_hooks.reviewer_did_show_question.append(on_show_question)
gui_hooks.reviewer_did_show_answer.append(on_show_answer)
gui_hooks.reviewer_did_show_question.append(on_reviewer_did_show_question)

setupHooks(None, ankimon_tracker_obj)

online_connectivity = test_online_connectivity()

#Connect to GitHub and Check for Notification and HelpGuideChanges
update_infos_md = addon_dir / "updateinfos.md"
def download_changelog():
    try:
        # URL of the file on GitHub
        github_url = f"https://raw.githubusercontent.com/h0tp-ftw/ankimon/refs/heads/main/assets/changelogs/{addon_ver}.md"
    
        # Read content from GitHub
        github_content = read_github_file(github_url)
    
        # If changelog content is None, try unknown.md as a fallback for all builds
        if github_content is None:
            github_url = "https://raw.githubusercontent.com/h0tp-ftw/ankimon/refs/heads/main/assets/changelogs/unknown.md"
            github_content = read_github_file(github_url)

        return github_content
    except Exception as e:
        return e

if online_connectivity and ssh:
    def done(result: Union[Exception, str, None]):
        if isinstance(result, Exception):
            show_warning_with_traceback(parent=mw, exception=result, message="Error connecting to GitHub:")
            return
        if result is None:
            showWarning("Failed to retrieve Ankimon content from GitHub.")
            return
        # Read content from the local file
        local_content = read_local_file(update_infos_md)
        # If local content is not the same as the GitHub content, open dialog
        if not compare_files(local_content, result):
            write_local_file(update_infos_md, result)
            dialog = UpdateNotificationWindow(markdown.markdown(result))
            if not no_more_news:
                dialog.exec()
    op = QueryOp(
        parent=mw,
        op=lambda _col: download_changelog(), # Background operation
        success=done, # Ran on UI thread
    ).without_collection().run_in_background()

def open_help_window(online_connectivity):
    try:
        # TODO: online_connectivity must be a function?
        # TODO: HelpWindow constructor must be empty?
        help_dialog = HelpWindow(online_connectivity)
        help_dialog.exec()
    except Exception as e:
        show_warning_with_traceback(parent=mw, exception=e, message="Error in opening Help Guide:")

def answerCard_before(filter, reviewer, card):
	utils.answBtnAmt = reviewer.mw.col.sched.answerButtons(card)
	return filter

# Globale Variable für die Zählung der Bewertungen

def answerCard_after(rev, card, ease):
    maxEase = rev.mw.col.sched.answerButtons(card)
    # Aktualisieren Sie die Zählung basierend auf der Bewertung
    if ease == 1:
        ankimon_tracker_obj.review("again")
    elif ease == maxEase - 2:
        ankimon_tracker_obj.review("hard")
    elif ease == maxEase - 1:
        ankimon_tracker_obj.review("good")
    elif ease == maxEase:
        ankimon_tracker_obj.review("easy")
    else:
        # default behavior for unforeseen cases
        tooltip("Error in ColorConfirmation: Couldn't interpret ease")
    ankimon_tracker_obj.reset_card_timer()

aqt.gui_hooks.reviewer_will_answer_card.append(answerCard_before)
aqt.gui_hooks.reviewer_did_answer_card.append(answerCard_after)


#get main pokemon details:
if database_complete:
    try:
        mainpokemon_name, mainpokemon_id, mainpokemon_ability, mainpokemon_type, mainpokemon_stats, mainpokemon_attacks, mainpokemon_level, mainpokemon_base_experience, mainpokemon_xp, mainpokemon_hp, mainpokemon_current_hp, mainpokemon_growth_rate, mainpokemon_ev, mainpokemon_iv, mainpokemon_evolutions, mainpokemon_battle_stats, mainpokemon_gender, mainpokemon_nickname = get_main_pokemon_data()
        starter = True
    except Exception:
        starter = False
        mainpokemon_level = 5
    #name, id, level, ability, type, stats, enemy_attacks, base_experience, growth_rate, ev, iv, gender, battle_status, battle_stats, tier, ev_yield, shiny = generate_random_pokemon()
    name, id, level, ability, type, base_stats, enemy_attacks, base_experience, growth_rate, ev, iv, gender, battle_status, battle_stats, tier, ev_yield, shiny = generate_random_pokemon(main_pokemon.level, ankimon_tracker_obj)
    pokemon_data = {
        'name': name,
        'id': id,
        'level': level,
        'ability': ability,
        'type': type,
        'base_stats': base_stats,
        'attacks': enemy_attacks,
        'base_experience': base_experience,
        'growth_rate': growth_rate,
        'ev': ev,
        'iv': iv,
        'gender': gender,
        'battle_status': battle_status,
        'battle_stats': battle_stats,
        'tier': tier,
        'ev_yield': ev_yield,
        'shiny': shiny
    }
    enemy_pokemon.update_stats(**pokemon_data)
    max_hp = enemy_pokemon.calculate_max_hp()
    enemy_pokemon.current_hp = max_hp
    enemy_pokemon.hp = max_hp
    enemy_pokemon.max_hp = max_hp
    ankimon_tracker_obj.randomize_battle_scene()

# Connect the hook to Anki's review event
gui_hooks.reviewer_did_answer_card.append(on_review_card)

if database_complete:
    badge_list = get_achieved_badges()
    if len(badge_list) > 1: # has atleast one badge
        rate_this_addon()

if database_complete:
    if mypokemon_path.is_file() is False:
        starter_window.display_starter_pokemon()
    else:
        with open(mypokemon_path, "r", encoding="utf-8") as file:
            pokemon_list = json.load(file)
            if not pokemon_list :
                starter_window.display_starter_pokemon()

count_items_and_rewrite(itembag_path)

#buttonlayout
# Create menu actions
# Create menu actions
create_menu_actions(
    database_complete,
    online_connectivity,
    None,#pokecollection_win,
    item_window,
    test_window,
    achievement_bag,
    open_team_builder,
    export_to_pkmn_showdown,
    export_all_pkmn_showdown,
    flex_pokemon_collection,
    eff_chart,
    gen_id_chart,
    credits,
    license,
    open_help_window,
    report_bug,
    rate_addon_url,
    version_dialog,
    trainer_card,
    ankimon_tracker_window,
    logger,
    data_handler_window,
    settings_window,
    shop_manager,
    pokedex_window,
    settings_obj.get("controls.key_for_opening_closing_ankimon"),
    join_discord_url,
    open_leaderboard_url,
    settings_obj,
    addon_dir,
    data_handler_obj,
    pokemon_pc,
    backup_manager,
)

    #https://goo.gl/uhAxsg
    #https://www.reddit.com/r/PokemonROMhacks/comments/9xgl7j/pokemon_sound_effects_collection_over_3200_sfx/
    #https://archive.org/details/pokemon-dp-sound-library-disc-2_202205
    #https://www.sounds-resource.com/nintendo_switch/pokemonswordshield/

# Define lists to hold hook functions
catch_pokemon_hooks = []
defeat_pokemon_hooks = []

# Function to add hooks to catch_pokemon event
def add_catch_pokemon_hook(func):
    catch_pokemon_hooks.append(func)

# Function to add hooks to defeat_pokemon event
def add_defeat_pokemon_hook(func):
    defeat_pokemon_hooks.append(func)

# Custom function that triggers the catch_pokemon hook
def CatchPokemonHook():
    if enemy_pokemon.hp < 1:
        catch_pokemon(enemy_pokemon, ankimon_tracker_obj, logger, "", collected_pokemon_ids, achievements)
        new_pokemon(enemy_pokemon, test_window, ankimon_tracker_obj, reviewer_obj)  # Show a new random Pokémon
    for hook in catch_pokemon_hooks:
        hook()

# Custom function that triggers the defeat_pokemon hook
def DefeatPokemonHook():
    if enemy_pokemon.hp < 1:
        kill_pokemon(main_pokemon, enemy_pokemon, evo_window, logger , achievements, trainer_card)
        new_pokemon(enemy_pokemon, test_window, ankimon_tracker_obj, reviewer_obj)  # Show a new random Pokémon
    for hook in defeat_pokemon_hooks:
        hook()

def on_profile_did_open():
    """Initialize services after profile is loaded."""
    # Show tip of the day
    try:
        show_tip_of_the_day()
    except Exception as e:
        show_warning_with_traceback(parent=mw, exception=e, message="Error showing tip of the day:")

    # Award monthly pokemon if applicable
    try:
        if online_connectivity:
            check_and_award_monthly_pokemon(logger)
        else:
            logger.log("info", "Skipping monthly pokemon check due to no internet connectivity.")
    except Exception as e:
        show_warning_with_traceback(parent=mw, exception=e, message="Error awarding monthly pokemon:")

    # AnkiWeb Sync
    try:
        ankiweb_sync = settings_obj.get("misc.ankiweb_sync")
        if not ankiweb_sync:
            logger.log("info", "AnkiWeb sync is disabled in settings - skipping sync system initialization")
            return

        # Set up sync hooks now that profile is available
        setup_ankimon_sync_hooks(settings_obj, logger)

        if not online_connectivity:
            logger.log("info", "No connection - AnkiWeb sync is disabled for this session")
        else: #if enabled and internet is available
            # Check for sync conflicts and show dialog if needed
            global sync_dialog
            sync_dialog = check_and_sync_pokemon_data(settings_obj, logger)
            logger.log("info", "Ankimon sync system initialized successfully")
    except Exception as e:
        show_warning_with_traceback(parent=mw, exception=e, message="Error setting up sync system:")

# Hook to expose the function
def on_profile_loaded():
    mw.defeatpokemon = DefeatPokemonHook
    mw.catchpokemon = CatchPokemonHook
    mw.add_catch_pokemon_hook = add_catch_pokemon_hook
    mw.add_defeat_pokemon_hook = add_defeat_pokemon_hook

# Add hook to run on profile load
addHook("profileLoaded", on_profile_loaded)

gui_hooks.profile_did_open.append(on_profile_did_open)
gui_hooks.profile_will_close.append(backup_manager.on_anki_close)

def catch_shortcut_function():
    if enemy_pokemon.hp < 1:
        catch_pokemon(enemy_pokemon, ankimon_tracker_obj, logger, "", collected_pokemon_ids, achievements)
        new_pokemon(enemy_pokemon, test_window, ankimon_tracker_obj, reviewer_obj)  # Show a new random Pokémon
    else:
        tooltip("You only catch a pokemon once it's fainted!")

def defeat_shortcut_function():
    if enemy_pokemon.hp < 1:
        kill_pokemon(main_pokemon, enemy_pokemon, evo_window, logger , achievements, trainer_card)
        new_pokemon(enemy_pokemon, test_window, ankimon_tracker_obj, reviewer_obj)  # Show a new random Pokémon
    else:
        tooltip("Wild pokemon has to be fainted to defeat it!")

catch_shortcut = catch_shortcut.lower()
defeat_shortcut = defeat_shortcut.lower()
#// adding shortcuts to _shortcutKeys function in anki
def _shortcutKeys_wrap(self, _old):
    original = _old(self)
    original.append((catch_shortcut, lambda: catch_shortcut_function()))
    original.append((defeat_shortcut, lambda: defeat_shortcut_function()))
    return original

Reviewer._shortcutKeys = wrap(Reviewer._shortcutKeys, _shortcutKeys_wrap, 'around')

if reviewer_buttons is True:
    #// Choosing styling for review other buttons in reviewer bottombar based on chosen style
    Review_linkHandelr_Original = Reviewer._linkHandler
    # Define the HTML and styling for the custom button
    def custom_button():
        return f"""<button title="Shortcut key: C" onclick="pycmd('catch');" {button_style}>Catch</button>"""

    # Update the link handler function to handle the custom button action
    def linkHandler_wrap(reviewer, url):
        if url == "catch":
            catch_shortcut_function()
        elif url == "defeat":
            defeat_shortcut_function()
        else:
            Review_linkHandelr_Original(reviewer, url)

    def _bottomHTML(self) -> str:
        return _bottomHTML_template % dict(
            edit=tr.studying_edit(),
            editkey=tr.actions_shortcut_key(val="E"),
            more=tr.studying_more(),
            morekey=tr.actions_shortcut_key(val="M"),
            downArrow=downArrow(),
            time=self.card.time_taken() // 1000,
            CatchKey=tr.actions_shortcut_key(val=f"{catch_shortcut}"),
            DefeatKey=tr.actions_shortcut_key(val=f"{defeat_shortcut}"),
        )

    # Replace the current HTML with the updated HTML
    Reviewer._bottomHTML = _bottomHTML  # Assuming you have access to self in this context
    # Replace the original link handler function with the modified one
    Reviewer._linkHandler = linkHandler_wrap

if settings_obj.get("misc.discord_rich_presence"):
    client_id = '1319014423876075541'  # Replace with your actual client ID
    large_image_url = "https://raw.githubusercontent.com/Unlucky-Life/ankimon/refs/heads/main/src/Ankimon/ankimon_logo.png"  # URL for the large image
    mw.ankimon_presence = DiscordPresence(client_id, large_image_url, ankimon_tracker_obj, logger, settings_obj)  # Establish connection and get the presence instance

    # Hook functions for Anki
    def on_reviewer_initialized(rev, card, ease):
        if mw.ankimon_presence:
            if mw.ankimon_presence.loop is False:
                mw.ankimon_presence.loop = True
                mw.ankimon_presence.start()
        else:
            client_id = '1319014423876075541'  # Replace with your actual client ID
            large_image_url = "https://raw.githubusercontent.com/Unlucky-Life/ankimon/refs/heads/main/src/Ankimon/ankimon_logo.png"  # URL for the large image
            mw.ankimon_presence = DiscordPresence(client_id, large_image_url, ankimon_tracker_obj, logger, settings_obj)  # Establish connection and get the presence instance
            mw.ankimon_presence.loop = True
            mw.ankimon_presence.start()

    def on_reviewer_will_end(*args):
        mw.ankimon_presence.loop = False
        mw.ankimon_presence.stop_presence()

    # Register the hook functions with Anki's GUI hooks
    gui_hooks.reviewer_did_answer_card.append(on_reviewer_initialized)
    gui_hooks.reviewer_will_end.append(mw.ankimon_presence.stop_presence)
    gui_hooks.sync_did_finish.append(mw.ankimon_presence.stop)
