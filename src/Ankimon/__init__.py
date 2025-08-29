"""
Ankimon Add-on Entry Point

This script is executed when Anki loads the add-on. It handles the initialization
of all necessary components, such as singletons and menu actions.
"""
from pathlib import Path

# Import singletons to ensure they are initialized
from . import singletons
# Import menu creation function
from .menu_buttons import create_menu_actions

# The creation of menu actions, which populates mw.pokemenu
create_menu_actions(
    database_complete=True,
    online_connectivity=False,
    pokecollection_win=singletons.pokecollection_win,
    item_window=singletons.item_window,
    test_window=singletons.test_window,
    achievement_bag=singletons.achievement_bag,
    open_team_builder=lambda: print("Mock callback: Team Builder"),
    export_to_pkmn_showdown=lambda: print("Mock callback: Export to Showdown"),
    export_all_pkmn_showdown=lambda: print("Mock callback: Export All to Showdown"),
    flex_pokemon_collection=lambda: print("Mock callback: Flex Collection"),
    eff_chart=singletons.eff_chart,
    gen_id_chart=singletons.gen_id_chart,
    credits=singletons.credits,
    license=singletons.license,
    open_help_window=lambda connectivity: print("Help window opened"),
    report_bug=lambda: print("Mock callback: Bug Report"),
    rate_addon_url=lambda: print("Mock callback: Rate Addon"),
    version_dialog=singletons.version_dialog,
    trainer_card=singletons.trainer_card,
    ankimon_tracker_window=singletons.ankimon_tracker_window,
    logger=singletons.logger,
    data_handler_window=singletons.data_handler_window,
    settings_window=singletons.settings_window,
    shop_manager=singletons.shop_manager,
    pokedex_window=singletons.pokedex_window,
    ankimon_key='Ctrl+K',
    join_discord_url=lambda: print("Mock callback: Join Discord"),
    open_leaderboard_url=lambda: print("Mock callback: Open Leaderboard"),
    settings_obj=singletons.settings_obj,
    addon_dir=Path(__file__).parent,
    data_handler_obj=singletons.data_handler_obj,
    pokemon_pc=singletons.pokemon_pc,
)

print("Ankimon add-on initialized via __init__.py")
