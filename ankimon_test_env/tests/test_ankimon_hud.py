#!/usr/bin/env python3
"""
Simple Ankimon HUD Test Script
This script focuses specifically on getting the Ankimon HUD (Pokemon sprites, HP bars, etc.) 
working in a test environment.
"""

import sys
import os
import types
from pathlib import Path

def setup_minimal_mocks():
    """Setup the absolute minimum mocks needed for Ankimon"""
    print("Setting up minimal mocks...")
    
    # Create basic anki/aqt mocks
    mock_anki = types.ModuleType("anki")
    mock_aqt = types.ModuleType("aqt")
    
    # Mock the essential classes
    from mock_anki.collection import Collection, MockCard
    mock_anki.collection = types.ModuleType("anki.collection")
    mock_anki.collection.Collection = Collection
    mock_anki.cards = types.ModuleType("anki.cards")
    mock_anki.cards.Card = MockCard
    
    # Mock aqt essentials
    mock_aqt.utils = types.ModuleType("aqt.utils")
    mock_aqt.utils.showInfo = lambda x: print(f"ShowInfo: {x}")
    mock_aqt.utils.showWarning = lambda x: print(f"ShowWarning: {x}")
    
    # Mock GUI hooks
    mock_aqt.gui_hooks = types.ModuleType("aqt.gui_hooks")
    mock_aqt.gui_hooks.reviewer_did_answer_card = []
    mock_aqt.gui_hooks.reviewer_will_end = []
    
    # Mock main window
    mw = types.SimpleNamespace()
    mw.col = Collection()
    mw.addonManager = types.SimpleNamespace()
    mw.addonManager.addonFromModule = lambda x: "ankimon"
    mw.addonManager.addonsFolder = lambda: Path(__file__).parent.parent / "src"
    
    mock_aqt.mw = mw
    
    # Inject into sys.modules
    sys.modules["anki"] = mock_anki
    sys.modules["anki.collection"] = mock_anki.collection
    sys.modules["anki.cards"] = mock_anki.cards
    sys.modules["aqt"] = mock_aqt
    sys.modules["aqt.utils"] = mock_aqt.utils
    sys.modules["aqt.gui_hooks"] = mock_aqt.gui_hooks
    sys.modules["aqt.main"] = mock_aqt
    
    return mw

def create_test_pokemon():
    """Create test Pokemon objects for the HUD"""
    print("Creating test Pokemon...")
    
    # Add Ankimon to path
    ankimon_path = Path(__file__).parent.parent / "src" / "Ankimon"
    if str(ankimon_path) not in sys.path:
        sys.path.insert(0, str(ankimon_path))
    
    # Create user files if they don't exist
    user_files = ankimon_path / "user_files"
    user_files.mkdir(exist_ok=True)
    
    # Create mock Pokemon data
    import json
    pokemon_data = [{
        "id": 25,
        "name": "Pikachu", 
        "level": 50,
        "hp": 80,
        "max_hp": 100,
        "shiny": False,
        "gender": "M"
    }]
    
    with open(user_files / "mypokemon.json", "w") as f:
        json.dump(pokemon_data, f)
    
    # Create basic settings
    settings_data = {
        "gui.show_mainpkmn_in_reviewer": 1,
        "battle.hp_bar_thickness": 3,
        "gui.reviewer_image_gif": 1
    }
    
    with open(user_files / "config.json", "w") as f:
        json.dump(settings_data, f)
    
    try:
        # Import Ankimon's Pokemon classes
        from pyobj.pokemon_obj import PokemonObject
        
        # Create main Pokemon (player's Pokemon)
        main_pokemon = PokemonObject(
            name="Pikachu",
            id=25,
            level=50,
            hp=80,
            stats={"hp": 100, "atk": 80, "def": 70, "spa": 90, "spd": 80, "spe": 120},
            shiny=False,
            gender="M"
        )
        
        # Create enemy Pokemon  
        enemy_pokemon = PokemonObject(
            name="Rattata",
            id=19, 
            level=15,
            hp=25,
            stats={"hp": 35, "atk": 56, "def": 35, "spa": 25, "spd": 35, "spe": 72},
            shiny=False,
            gender="F"
        )
        
        return main_pokemon, enemy_pokemon
        
    except ImportError as e:
        print(f"Could not import Pokemon classes: {e}")
        return None, None

def create_test_hud(main_pokemon, enemy_pokemon):
    """Create and test the Ankimon HUD system"""
    print("Setting up HUD system...")
    
    try:
        # Import required Ankimon components
        from pyobj.settings import Settings
        from pyobj.reviewer_obj import Reviewer_Manager
        from pyobj.ankimon_tracker import AnkimonTracker
        
        # Create settings
        settings_obj = Settings()
        
        # Create tracker (needed by reviewer manager)
        tracker = AnkimonTracker(trainer_card=None, settings_obj=settings_obj)
        tracker.set_main_pokemon(main_pokemon)
        tracker.set_enemy_pokemon(enemy_pokemon)
        
        # Create the reviewer manager (this handles HUD injection)
        reviewer_manager = Reviewer_Manager(
            settings_obj=settings_obj,
            main_pokemon=main_pokemon,
            enemy_pokemon=enemy_pokemon,
            ankimon_tracker=tracker
        )
        
        print("HUD system created successfully!")
        return reviewer_manager
        
    except ImportError as e:
        print(f"Could not import HUD components: {e}")
        return None

def test_hud_injection(reviewer_manager):
    """Test the HUD injection functionality"""
    print("Testing HUD injection...")
    
    if not reviewer_manager:
        print("No reviewer manager available")
        return
    
    # Create a mock reviewer and card for testing
    mock_reviewer = types.SimpleNamespace()
    mock_reviewer.web = types.SimpleNamespace()
    mock_reviewer.web.eval = lambda js: print(f"JavaScript executed: {js[:100]}...")
    
    from mock_anki.collection import MockCard
    mock_card = MockCard(1, "Test Question", "Test Answer")
    
    try:
        # Call the HUD update function (this is what normally happens when a card is answered)
        reviewer_manager.update_life_bar(mock_reviewer, mock_card, 3)
        print("HUD injection test completed!")
        
    except Exception as e:
        print(f"HUD injection failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("=== Ankimon HUD Test ===")
    
    # Setup mocks
    mw = setup_minimal_mocks()
    
    # Create Pokemon
    main_pokemon, enemy_pokemon = create_test_pokemon()
    if not main_pokemon:
        print("Failed to create Pokemon objects")
        return
    
    print(f"Created Pokemon - Main: {main_pokemon.name}, Enemy: {enemy_pokemon.name}")
    
    # Setup HUD
    reviewer_manager = create_test_hud(main_pokemon, enemy_pokemon)
    
    # Test HUD injection
    test_hud_injection(reviewer_manager)
    
    print("\n=== Test completed ===")
    print("If you saw JavaScript execution messages above, the HUD system is working!")
    print("Next step: Run this in a full Qt environment to see the visual HUD")

if __name__ == "__main__":
    main()