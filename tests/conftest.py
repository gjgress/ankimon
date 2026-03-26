import sys
from unittest.mock import MagicMock
import pytest
import os

@pytest.fixture(autouse=True, scope="session")
def setup_ankimon_mocks():
    """
    Globally mock all Anki, PyQt, and external dependencies required for testing Ankimon logic.
    This ensures these are mocked before any module is loaded.
    """
    for mod in [
        'aqt', 'aqt.mw', 'aqt.utils', 'aqt.qt', 'aqt.operations', 'aqt.reviewer',
        'aqt.webview', 'aqt.gui_hooks', 'aqt.theme', 'anki', 'anki.hooks',
        'anki.buildinfo', 'anki.utils', 'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtGui',
        'PyQt6.QtCore', 'PyQt6.QtMultimedia', 'PyQt6.QtNetwork', 'PyQt6.QtWebEngineCore',
        'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebChannel', 'markdown', 'requests'
    ]:
        if mod not in sys.modules:
            sys.modules[mod] = MagicMock()

    sys.modules['aqt'].mw = MagicMock()
    sys.modules['aqt.qt'].QDialog = MagicMock
    sys.modules['aqt.qt'].QDialog.DialogCode = MagicMock()
    sys.modules['aqt.qt'].QDialog.DialogCode.Accepted = 1
    sys.modules['anki.buildinfo'].version = "2.1.0"

    class MockPackage(MagicMock):
        __path__ = []

    for pkg in [
        'Ankimon.singletons', 'Ankimon.gui_classes', 'Ankimon.pyobj', 'Ankimon.pokedex',
        'Ankimon.gui_classes.overview_team', 'Ankimon.gui_classes.choose_trainer_sprite_graphical',
        'Ankimon.gui_classes.pokemon_team_window', 'Ankimon.gui_classes.check_files',
        'Ankimon.gui_classes.pokemon_details', 'Ankimon.gui_classes.pokedex',
        'Ankimon.gui_classes.pokemon_pc_box', 'Ankimon.gui_classes.starter_pokemon',
        'Ankimon.gui_classes.evolution', 'Ankimon.gui_classes.backup_manager_dialog',
        'Ankimon.pyobj.trainer_card_window', 'Ankimon.pyobj.download_sprites',
        'Ankimon.pyobj.ankimon_leaderboard', 'Ankimon.pyobj.settings', 'Ankimon.pyobj.translator',
        'Ankimon.pyobj.InfoLogger', 'Ankimon.pyobj.collection_dialog', 'Ankimon.pyobj.item_window',
        'Ankimon.pyobj.pc_box', 'Ankimon.pyobj.trainer_card', 'Ankimon.pyobj.data_handler_window',
        'Ankimon.pyobj.settings_window', 'Ankimon.pyobj.test_window', 'Ankimon.pyobj.data_handler',
        'Ankimon.pyobj.ankimon_shop', 'Ankimon.pyobj.achievement_window', 'Ankimon.pyobj.ankimon_tracker_window',
        'Ankimon.pyobj.backup_manager', 'Ankimon.pyobj.help_window', 'Ankimon.pyobj.backup_files',
        'Ankimon.pyobj.ankimon_sync', 'Ankimon.pyobj.tip_of_the_day', 'Ankimon.pyobj.pokemon_trade',
        'Ankimon.pyobj.error_handler', 'Ankimon.pokedex.pokedex_obj', 'Ankimon.pyobj.pokemon_obj',
        'Ankimon.pyobj.ankimon_tracker', 'Ankimon.pyobj.reviewer_obj',
        'Ankimon.pyobj.evolution_window', 'Ankimon.pyobj.starter_window',
        'Ankimon.classes.choose_move_dialog', 'Ankimon.pyobj.attack_dialog'
    ]:
        if pkg not in sys.modules:
            sys.modules[pkg] = MockPackage()

    sys.path.insert(0, os.path.abspath('src'))

    # Setup main_pokemon mock to have a level that can be used in arithmetic operations
    mock_main_pokemon = MagicMock()
    mock_main_pokemon.level = 10
    sys.modules['Ankimon.singletons'].main_pokemon = mock_main_pokemon

    # Also mock generate_random_pokemon to prevent executing the actual code
    mock_encounter_functions = MagicMock()
    mock_encounter_functions.generate_random_pokemon.return_value = (
        "Rattata", 19, 5, "Run Away", ["Normal"], {}, ["Tackle"], 58, "medium-slow",
        {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0},
        {"hp": 0, "atk": 0, "def": 0, "spa": 0, "spd": 0, "spe": 0},
        "M", "fighting", {}, "Common", {}, False
    )
    sys.modules['Ankimon.functions.encounter_functions'] = mock_encounter_functions
