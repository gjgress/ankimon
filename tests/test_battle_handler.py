from unittest.mock import MagicMock, patch

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
