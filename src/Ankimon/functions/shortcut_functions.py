# -*- coding: utf-8 -*-
"""
Shortcut functions and hook wrappers for Ankimon.

Contains keyboard shortcut handlers and custom hook management for catch/defeat actions.
"""

from anki.hooks import wrap
from aqt.reviewer import Reviewer
from aqt.utils import tooltip

from .encounter_functions import catch_pokemon, kill_pokemon, new_pokemon


# Define lists to hold hook functions
catch_pokemon_hooks = []
defeat_pokemon_hooks = []


def add_catch_pokemon_hook(func):
    """Add a function to be called when a Pokemon is caught."""
    catch_pokemon_hooks.append(func)


def add_defeat_pokemon_hook(func):
    """Add a function to be called when a Pokemon is defeated."""
    defeat_pokemon_hooks.append(func)


def create_catch_pokemon_hook(enemy_pokemon, ankimon_tracker_obj, logger, collected_pokemon_ids, 
                               achievements, main_pokemon, test_window, reviewer_obj):
    """
    Create and return the CatchPokemonHook function with the required context.
    """
    def CatchPokemonHook():
        if enemy_pokemon.hp < 1:
            catch_pokemon(enemy_pokemon, ankimon_tracker_obj, logger, "", collected_pokemon_ids, achievements, main_pokemon)
            new_pokemon(enemy_pokemon, test_window, ankimon_tracker_obj, reviewer_obj)
        for hook in catch_pokemon_hooks:
            hook()
    return CatchPokemonHook


def create_defeat_pokemon_hook(enemy_pokemon, main_pokemon, evo_window, logger, 
                                achievements, trainer_card, test_window, ankimon_tracker_obj, reviewer_obj):
    """
    Create and return the DefeatPokemonHook function with the required context.
    """
    def DefeatPokemonHook():
        if enemy_pokemon.hp < 1:
            kill_pokemon(main_pokemon, enemy_pokemon, evo_window, logger, achievements, trainer_card)
            new_pokemon(enemy_pokemon, test_window, ankimon_tracker_obj, reviewer_obj)
        for hook in defeat_pokemon_hooks:
            hook()
    return DefeatPokemonHook


def create_catch_shortcut_function(enemy_pokemon, ankimon_tracker_obj, logger, 
                                    collected_pokemon_ids, achievements, main_pokemon, 
                                    test_window, reviewer_obj):
    """
    Create and return the catch shortcut function with the required context.
    """
    def catch_shortcut_function():
        if enemy_pokemon.hp < 1:
            catch_pokemon(enemy_pokemon, ankimon_tracker_obj, logger, "", collected_pokemon_ids, achievements, main_pokemon)
            new_pokemon(enemy_pokemon, test_window, ankimon_tracker_obj, reviewer_obj)
        else:
            tooltip("You only catch a pokemon once it's fainted!")
    return catch_shortcut_function


def create_defeat_shortcut_function(enemy_pokemon, main_pokemon, evo_window, logger,
                                     achievements, trainer_card, test_window, 
                                     ankimon_tracker_obj, reviewer_obj):
    """
    Create and return the defeat shortcut function with the required context.
    """
    def defeat_shortcut_function():
        if enemy_pokemon.hp < 1:
            kill_pokemon(main_pokemon, enemy_pokemon, evo_window, logger, achievements, trainer_card)
            new_pokemon(enemy_pokemon, test_window, ankimon_tracker_obj, reviewer_obj)
        else:
            tooltip("Wild pokemon has to be fainted to defeat it!")
    return defeat_shortcut_function


def create_item_shortcut_function(main_pokemon, mw, QuickItemDialog):
    """
    Create and return the item shortcut function with the required context.
    """
    def item_shortcut_function():
        """Open quick item use dialog"""
        dialog = QuickItemDialog(main_pokemon, mw)
        dialog.exec()
    return item_shortcut_function


def setup_reviewer_shortcuts(catch_shortcut, defeat_shortcut, item_shortcut,
                              catch_func, defeat_func, item_func):
    """
    Set up the keyboard shortcuts for the reviewer.
    
    Args:
        catch_shortcut: Key for catching Pokemon
        defeat_shortcut: Key for defeating Pokemon  
        item_shortcut: Key for quick item use
        catch_func: Function to call for catch
        defeat_func: Function to call for defeat
        item_func: Function to call for item use
    """
    catch_key = catch_shortcut.lower()
    defeat_key = defeat_shortcut.lower()
    item_key = item_shortcut.lower() if item_shortcut else "7"
    
    def _shortcutKeys_wrap(self, _old):
        original = _old(self)
        original.append((catch_key, lambda: catch_func()))
        original.append((defeat_key, lambda: defeat_func()))
        original.append((item_key, lambda: item_func()))
        return original
    
    Reviewer._shortcutKeys = wrap(Reviewer._shortcutKeys, _shortcutKeys_wrap, 'around')
