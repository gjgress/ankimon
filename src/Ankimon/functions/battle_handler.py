import random
import copy
from aqt.qt import QDialog
from aqt import mw

from ..utils import (
    safe_get_random_move,
    play_effect_sound,
    play_sound,
)

from ..singletons import (
    reviewer_obj,
    logger,
    settings_obj,
    translator,
    main_pokemon,
    enemy_pokemon,
    ankimon_tracker_obj,
    test_window,
    evo_window,
    trainer_card
)

from ..functions.badges_functions import handle_review_count_achievement, check_for_badge, receive_badge
from ..functions.drawing_utils import tooltipWithColour
from ..functions.encounter_functions import handle_enemy_faint, handle_main_pokemon_faint
from ..classes.choose_move_dialog import MoveSelectionDialog
from ..poke_engine.ankimon_hooks_to_poke_engine import simulate_battle_with_poke_engine
from ..functions.battle_functions import update_pokemon_battle_status, validate_pokemon_status, process_battle_data
from ..pyobj.error_handler import show_warning_with_traceback

# Global state for battle
cry_counter = 0
item_receive_value = random.randint(3, 385)

new_state = None
mutator_full_reset = 1
user_hp_after = 0
opponent_hp_after = 0
dmg_from_enemy_move = 0
dmg_from_user_move = 0

def _get_cards_per_round() -> int:
    cards_per_round = settings_obj.get("battle.cards_per_round")

    if isinstance(cards_per_round, int):
        return cards_per_round

    # If it's a string in "number-number" format, return random value between bounds
    if isinstance(cards_per_round, str) and "-" in cards_per_round:
        try:
            min_val, max_val = map(int, cards_per_round.split("-"))
            random_value = random.randint(min_val, max_val)
            return random_value
        except (ValueError, IndexError):
            return 2

    return 2

# Hook into Anki's card review event
def on_review_card(*args):
    try:
        global cry_counter
        global item_receive_value
        global new_state
        global mutator_full_reset
        global user_hp_after
        global opponent_hp_after
        global dmg_from_enemy_move
        global dmg_from_user_move

        # Also need achievements to be updated and from singletons but they get reassigned
        from ..singletons import achievements as current_achievements
        achievements = current_achievements
        from ..__init__ import collected_pokemon_ids

        multiplier = ankimon_tracker_obj.multiplier
        if main_pokemon.attacks:
            user_attack = random.choice(main_pokemon.attacks)
        else:
            user_attack = "splash"
        if enemy_pokemon.attacks:
            enemy_attack = random.choice(enemy_pokemon.attacks)
        else:
            enemy_attack = "splash"

        battle_sounds = settings_obj.get("audio.battle_sounds")

        # Increment the counter when a card is reviewed
        ankimon_tracker_obj.cards_battle_round += 1
        ankimon_tracker_obj.cry_counter += 1
        cry_counter = ankimon_tracker_obj.cry_counter
        total_reviews = ankimon_tracker_obj.total_reviews
        reviewer_obj.seconds = 0
        reviewer_obj.myseconds = 0
        ankimon_tracker_obj.general_card_count_for_battle += 1

        color = "#F0B27A" # Initialize with a default color

        # Handle achievements based on total reviews
        achievements = handle_review_count_achievement(total_reviews, achievements)

        item_receive_value -= 1
        if item_receive_value <= 0:
            item_receive_value = random.randint(3, 385)

            test_window.display_item()

            # Give them a badge for getting an item
            if not check_for_badge(achievements,6):
                receive_badge(6, achievements)

        if total_reviews == settings_obj.get("battle.daily_average"):
            settings_obj.set("trainer.cash", settings_obj.get("trainer.cash") + 200)
            trainer_card.cash = settings_obj.get("trainer.cash")

        if battle_sounds and ankimon_tracker_obj.general_card_count_for_battle == 1:
            play_sound(enemy_pokemon.id, settings_obj)

        if ankimon_tracker_obj.cards_battle_round >= _get_cards_per_round():
            ankimon_tracker_obj.cards_battle_round = 0
            ankimon_tracker_obj.attack_counter = 0
            ankimon_tracker_obj.pokemon_encouter += 1
            multiplier = ankimon_tracker_obj.multiplier

            if ankimon_tracker_obj.pokemon_encouter > 0 and enemy_pokemon.hp > 0 and multiplier < 1:
                enemy_move = safe_get_random_move(enemy_pokemon.attacks, logger=logger)
                enemy_move_category = enemy_move.get("category")

                if enemy_move_category == "Status":
                    color = "#F7DC6F"
                elif enemy_move_category == "Special":
                    color = "#D2B4DE"
                else:
                    color = "#F0B27A"

            else:
                enemy_attack = "splash" # if enemy will NOT attack, it uses SPLASH

            move = safe_get_random_move(main_pokemon.attacks, logger=logger)
            category = move.get("category")

            if ankimon_tracker_obj.pokemon_encouter > 0 and main_pokemon.hp > 0 and enemy_pokemon.hp > 0:

                if settings_obj.get("controls.allow_to_choose_moves"):
                    dialog = MoveSelectionDialog(main_pokemon.attacks)
                    if dialog.exec() == QDialog.DialogCode.Accepted:
                        if dialog.selected_move:
                            user_attack = dialog.selected_move

                if category == "Status":
                    color = "#F7DC6F"

                elif category == "Special":
                    color = "#D2B4DE"

                else:
                    color = "#F0B27A"

            '''
            To the devs,
            below is the MOST IMPORTANT function for the new engine.
            This runs our current Pokemon stats through the SirSkaro Poke-Engine.
            The "results" can then be used to access battle outcomes.
            '''

            results = simulate_battle_with_poke_engine(
                main_pokemon,
                enemy_pokemon,
                user_attack,
                enemy_attack,
                mutator_full_reset,
                new_state,
            )

            # 2. Unpack results from the simulation
            battle_info = results[0]
            new_state = copy.deepcopy(results[1])
            dmg_from_enemy_move = results[2]  # NOTE : This is ACTUALLY the sum of all damages and heals that occured to the user during the turn
            dmg_from_user_move = results[3]
            mutator_full_reset = results[4]
            current_battle_info_changes = results[5]
            instructions = results[0]["instructions"]
            heals_to_user = sum([inst[2] for inst in instructions if inst[0:2] == ['heal', 'user']])
            heals_to_opponent = sum([inst[2] for inst in instructions if inst[0:2] == ['heal', 'opponent']])
            true_dmg_from_enemy_move = sum([inst[2] for inst in instructions if inst[0:2] == ['damage', 'user']])
            true_dmg_from_user_move = sum([inst[2] for inst in instructions if inst[0:2] == ['damage', 'opponent']])

            # workaround for the DAMAGE being negative in some cases
            if true_dmg_from_enemy_move < 0:
                true_dmg_from_enemy_move = 0
                heals_to_user += abs(true_dmg_from_enemy_move)  # Add the negative damage as a heal
            if true_dmg_from_user_move < 0:
                true_dmg_from_user_move = 0
                heals_to_opponent += abs(true_dmg_from_user_move)

            # 3. --- IMMEDIATE STATE SYNCHRONIZATION (THE FIX) ---
            # Update Pokémon objects with the new state from the engine BEFORE any other processing.
            # This ensures all subsequent functions have the correct HP and status.
            main_pokemon.hp = new_state.user.active.hp
            main_pokemon.current_hp = new_state.user.active.hp
            enemy_pokemon.hp = new_state.opponent.active.hp
            enemy_pokemon.current_hp = new_state.opponent.active.hp

            # Update statuses based on instructions, now that HP is correct.
            enemy_status_changed, main_status_changed = update_pokemon_battle_status(
                battle_info, enemy_pokemon, main_pokemon
            )

            # Final validation to ensure consistency
            enemy_pokemon.battle_status = validate_pokemon_status(enemy_pokemon)
            main_pokemon.battle_status = validate_pokemon_status(main_pokemon)

            # 4. Generate the battle log message using the now-correct Pokémon states
            formatted_battle_log = process_battle_data(
                battle_info=battle_info,
                multiplier=multiplier,
                main_pokemon=main_pokemon,
                enemy_pokemon=enemy_pokemon,
                user_attack=user_attack,
                enemy_attack=enemy_attack,
                dmg_from_user_move=true_dmg_from_user_move,
                dmg_from_enemy_move=true_dmg_from_enemy_move,
                user_hp_after=main_pokemon.hp, # Use the already updated HP
                opponent_hp_after=enemy_pokemon.hp, # Use the already updated HP
                battle_status=main_pokemon.battle_status,
                pokemon_encounter=ankimon_tracker_obj.pokemon_encouter,
                translator=translator,
                changes=current_battle_info_changes,
            )

            # Display the complete message
            tooltipWithColour(formatted_battle_log, color)

            # Handle sound effects and animations (existing code)
            if true_dmg_from_enemy_move > 0 and multiplier < 1:
                reviewer_obj.myseconds = settings_obj.compute_special_variable("animate_time")
                tooltipWithColour(f" -{true_dmg_from_enemy_move} HP ", "#F06060", x=-200)
                play_effect_sound(settings_obj, "HurtNormal")

            if true_dmg_from_user_move > 0:
                reviewer_obj.seconds = settings_obj.compute_special_variable("animate_time")
                tooltipWithColour(f" -{true_dmg_from_user_move} HP ", "#F06060", x=200)
                if multiplier == 1:
                    play_effect_sound(settings_obj, "HurtNormal")
                elif multiplier < 1:
                    play_effect_sound(settings_obj, "HurtNotEffective")
                elif multiplier > 1:
                    play_effect_sound(settings_obj, "HurtSuper")
            else:
                reviewer_obj.seconds = 0

            if int(heals_to_user) != 0:
                # "Negative heal" can happen sometimes. That's how the Life Orb item deals its damage for instance
                heal_color = "#68FA94" if heals_to_user > 0 else "#F06060"
                sign = "+" if heals_to_user > 0 else ""
                tooltipWithColour(f" {sign}{int(heals_to_user)} HP ", heal_color, x=-250)

            if int(heals_to_opponent) != 0:
                # "Negative heal" can happen sometimes. That's how the Life Orb item deals its damage for instance
                heal_color = "#68FA94" if heals_to_opponent > 0 else "#F06060"
                sign = "+" if heals_to_opponent > 0 else ""
                tooltipWithColour(f" {sign}{int(heals_to_opponent)} HP ", heal_color, x=250)

            # if enemy pokemon faints, this handles AUTOMATIC BATTLE
            if enemy_pokemon.hp < 1:
                enemy_pokemon.hp = 0
                test_window.display_battle()
                handle_enemy_faint(
                    main_pokemon,
                    enemy_pokemon,
                    collected_pokemon_ids,
                    test_window,
                    evo_window,
                    reviewer_obj,
                    logger,
                    achievements
                    )

                mutator_full_reset = 1 # reset opponent state

        if cry_counter == 10 and battle_sounds is True:
            cry_counter = 0
            play_sound(enemy_pokemon.id, settings_obj)

        # user pokemon faints
        if main_pokemon.hp < 1:
            handle_main_pokemon_faint(main_pokemon, enemy_pokemon, test_window, reviewer_obj, translator)
            mutator_full_reset = 1 # fully reset battle state

        class Container(object):
            pass

        reviewer = Container()
        reviewer.web = mw.reviewer.web
        reviewer_obj.update_life_bar(reviewer, 0, 0)
        if test_window is not None:
            if enemy_pokemon.hp > 0:
                test_window.display_battle()

    except Exception as e:
        show_warning_with_traceback(parent=mw, exception=e, message="An error occurred in reviewer:")
