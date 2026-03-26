import sys
import types
from unittest.mock import MagicMock, patch
import pytest

# Mock everything early so the module can just import mock objects
for mod in [
    'aqt', 'aqt.mw', 'aqt.utils', 'aqt.qt', 'aqt.operations', 'aqt.reviewer',
    'aqt.webview', 'aqt.gui_hooks', 'aqt.theme', 'anki', 'anki.hooks',
    'anki.buildinfo', 'anki.utils', 'PyQt6', 'PyQt6.QtWidgets', 'PyQt6.QtGui',
    'PyQt6.QtCore', 'PyQt6.QtMultimedia', 'PyQt6.QtNetwork', 'PyQt6.QtWebEngineCore',
    'PyQt6.QtWebEngineWidgets', 'PyQt6.QtWebChannel', 'markdown', 'requests'
]:
    sys.modules[mod] = MagicMock()

# Setup some specific mock structures
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
    sys.modules[pkg] = MockPackage()


import os
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

def test_battle_handler_damage_calculation(monkeypatch):
    from Ankimon.functions.battle_handler import on_review_card

    with patch('Ankimon.functions.battle_handler.settings_obj') as mock_settings, \
         patch('Ankimon.functions.battle_handler.main_pokemon') as mock_main, \
         patch('Ankimon.functions.battle_handler.enemy_pokemon') as mock_enemy, \
         patch('Ankimon.functions.battle_handler.ankimon_tracker_obj') as mock_tracker, \
         patch('Ankimon.functions.battle_handler.reviewer_obj') as mock_reviewer, \
         patch('Ankimon.functions.battle_handler.simulate_battle_with_poke_engine') as mock_simulate, \
         patch('Ankimon.functions.battle_handler.test_window') as mock_test_window:

        # Setup mocks
        mock_settings.get.side_effect = lambda k: {
            "battle.cards_per_round": 1,
            "battle.daily_average": 100,
            "audio.battle_sounds": False,
            "controls.allow_to_choose_moves": False
        }.get(k, None)

        mock_main.hp = 100
        mock_main.attacks = ["Tackle"]
        mock_main.type = ["Normal"]
        mock_main.name = "Pikachu"
        mock_main.battle_status = "fighting"

        mock_enemy.hp = 100
        mock_enemy.attacks = ["Tackle"]
        mock_enemy.id = 1
        mock_enemy.name = "Bulbasaur"
        mock_enemy.battle_status = "fighting"

        mock_tracker.multiplier = 1.0
        mock_tracker.attack_counter = 0
        mock_tracker.cards_battle_round = 0
        mock_tracker.cry_counter = 0
        mock_tracker.total_reviews = 10
        mock_tracker.general_card_count_for_battle = 0
        mock_tracker.pokemon_encouter = 1

        # Prepare the mock engine result
        mock_battle_info = {'instructions': [
            ['damage', 'opponent', 20],
            ['damage', 'user', 10]
        ]}
        mock_new_state = MagicMock()
        mock_new_state.user.active.hp = 90
        mock_new_state.opponent.active.hp = 80

        mock_simulate.return_value = (
            mock_battle_info,
            mock_new_state,
            10, # dmg_from_enemy_move
            20, # dmg_from_user_move
            1,  # mutator_full_reset
            []  # changes
        )

        # We need to mock some internal functions that cause issues during tests
        with patch('Ankimon.functions.battle_handler.update_pokemon_battle_status', return_value=(False, False)), \
             patch('Ankimon.functions.battle_handler.validate_pokemon_status', return_value="fighting"), \
             patch('Ankimon.functions.battle_handler.process_battle_data', return_value="Battle Message"), \
             patch('Ankimon.functions.battle_handler.tooltipWithColour'), \
             patch('Ankimon.functions.battle_handler.handle_review_count_achievement'), \
             patch('Ankimon.functions.battle_handler.trainer_card'):

            # Execute
            on_review_card()

            # Assert that simulate was called
            mock_simulate.assert_called_once()

            # Assert HP was updated correctly from the mock state
            assert mock_main.hp == 90
            assert mock_enemy.hp == 80

def test_battle_handler_enemy_faint(monkeypatch):
    from Ankimon.functions.battle_handler import on_review_card

    with patch('Ankimon.functions.battle_handler.settings_obj') as mock_settings, \
         patch('Ankimon.functions.battle_handler.main_pokemon') as mock_main, \
         patch('Ankimon.functions.battle_handler.enemy_pokemon') as mock_enemy, \
         patch('Ankimon.functions.battle_handler.ankimon_tracker_obj') as mock_tracker, \
         patch('Ankimon.functions.battle_handler.simulate_battle_with_poke_engine') as mock_simulate, \
         patch('Ankimon.functions.battle_handler.handle_enemy_faint') as mock_handle_enemy_faint:

        # Setup mocks
        mock_settings.get.side_effect = lambda k: {
            "battle.cards_per_round": 1,
            "battle.daily_average": 100,
            "audio.battle_sounds": False,
            "controls.allow_to_choose_moves": False
        }.get(k, None)

        mock_main.hp = 100
        mock_main.attacks = ["Tackle"]
        mock_enemy.hp = 10 # Start with low HP
        mock_enemy.attacks = ["Tackle"]

        mock_tracker.multiplier = 1.0
        mock_tracker.attack_counter = 0
        mock_tracker.cards_battle_round = 0
        mock_tracker.cry_counter = 0
        mock_tracker.total_reviews = 10
        mock_tracker.general_card_count_for_battle = 0
        mock_tracker.pokemon_encouter = 1

        mock_new_state = MagicMock()
        mock_new_state.user.active.hp = 90
        mock_new_state.opponent.active.hp = 0 # Enemy faints

        mock_simulate.return_value = (
            {'instructions': []}, mock_new_state, 10, 100, 1, []
        )

        with patch('Ankimon.functions.battle_handler.update_pokemon_battle_status', return_value=(False, False)), \
             patch('Ankimon.functions.battle_handler.validate_pokemon_status', return_value="fainted"), \
             patch('Ankimon.functions.battle_handler.process_battle_data'), \
             patch('Ankimon.functions.battle_handler.tooltipWithColour'), \
             patch('Ankimon.functions.battle_handler.handle_review_count_achievement'), \
             patch('Ankimon.functions.battle_handler.trainer_card'):

            # Execute
            on_review_card()

            # Assert enemy faint logic was triggered
            assert mock_enemy.hp == 0
            mock_handle_enemy_faint.assert_called_once()

def test_battle_handler_main_faint(monkeypatch):
    from Ankimon.functions.battle_handler import on_review_card

    with patch('Ankimon.functions.battle_handler.settings_obj') as mock_settings, \
         patch('Ankimon.functions.battle_handler.main_pokemon') as mock_main, \
         patch('Ankimon.functions.battle_handler.enemy_pokemon') as mock_enemy, \
         patch('Ankimon.functions.battle_handler.ankimon_tracker_obj') as mock_tracker, \
         patch('Ankimon.functions.battle_handler.simulate_battle_with_poke_engine') as mock_simulate, \
         patch('Ankimon.functions.battle_handler.handle_main_pokemon_faint') as mock_handle_main_faint:

        # Setup mocks
        mock_settings.get.side_effect = lambda k: {
            "battle.cards_per_round": 1,
            "battle.daily_average": 100,
            "audio.battle_sounds": False,
            "controls.allow_to_choose_moves": False
        }.get(k, None)

        mock_main.hp = 10 # Start with low HP
        mock_main.attacks = ["Tackle"]
        mock_enemy.hp = 100
        mock_enemy.attacks = ["Tackle"]

        mock_tracker.multiplier = 1.0
        mock_tracker.attack_counter = 0
        mock_tracker.cards_battle_round = 0
        mock_tracker.cry_counter = 0
        mock_tracker.total_reviews = 10
        mock_tracker.general_card_count_for_battle = 0
        mock_tracker.pokemon_encouter = 1

        mock_new_state = MagicMock()
        mock_new_state.user.active.hp = 0 # Main faints
        mock_new_state.opponent.active.hp = 90

        mock_simulate.return_value = (
            {'instructions': []}, mock_new_state, 100, 10, 1, []
        )

        with patch('Ankimon.functions.battle_handler.update_pokemon_battle_status', return_value=(False, False)), \
             patch('Ankimon.functions.battle_handler.validate_pokemon_status', return_value="fainted"), \
             patch('Ankimon.functions.battle_handler.process_battle_data'), \
             patch('Ankimon.functions.battle_handler.tooltipWithColour'), \
             patch('Ankimon.functions.battle_handler.handle_review_count_achievement'), \
             patch('Ankimon.functions.battle_handler.trainer_card'):

            # Execute
            on_review_card()

            # Assert main faint logic was triggered
            assert mock_main.hp == 0
            mock_handle_main_faint.assert_called_once()
