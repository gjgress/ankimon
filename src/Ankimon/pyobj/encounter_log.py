"""
Encounter Log System for Ankimon

Tracks Pokemon encounters with timestamps and battle outcomes.
Also provides functions to update individual Pokemon battle stats.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
from aqt import mw

from ..resources import encounter_log_path, mypokemon_path

# Maximum number of encounters to keep in the log
MAX_ENCOUNTER_LOG_SIZE = 100


def load_encounter_log() -> List[Dict[str, Any]]:
    """Load the encounter log from file."""
    try:
        if encounter_log_path.is_file():
            with open(encounter_log_path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        print(f"Ankimon: Error loading encounter log: {e}")
    return []


def save_encounter_log(log: List[Dict[str, Any]]) -> None:
    """Save the encounter log to file."""
    try:
        with open(encounter_log_path, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2)
    except Exception as e:
        print(f"Ankimon: Error saving encounter log: {e}")


def log_encounter(
    pokemon_id: int,
    pokemon_name: str,
    level: int,
    tier: str,
    is_shiny: bool,
    outcome: str,  # "caught", "defeated", "fled", "lost"
    main_pokemon_name: Optional[str] = None,
    main_pokemon_id: Optional[str] = None,  # individual_id
) -> None:
    """
    Log a Pokemon encounter with timestamp and outcome.
    
    Args:
        pokemon_id: The Pokedex ID of the encountered Pokemon
        pokemon_name: Name of the encountered Pokemon
        level: Level of the encountered Pokemon
        tier: Tier of the Pokemon (Normal, Legendary, etc.)
        is_shiny: Whether the Pokemon was shiny
        outcome: The result of the encounter ("caught", "defeated", "fled", "lost")
        main_pokemon_name: Name of the main Pokemon used (optional)
        main_pokemon_id: Individual ID of the main Pokemon used (optional)
    """
    log = load_encounter_log()
    
    entry = {
        "timestamp": datetime.now().isoformat(),
        "pokemon_id": pokemon_id,
        "pokemon_name": pokemon_name.capitalize() if pokemon_name else "Unknown",
        "level": level,
        "tier": tier,
        "shiny": is_shiny,
        "outcome": outcome,
        "main_pokemon_name": main_pokemon_name.capitalize() if main_pokemon_name else None,
        "main_pokemon_individual_id": main_pokemon_id,
    }
    
    # Add to the beginning of the log (most recent first)
    log.insert(0, entry)
    
    # Trim log if it exceeds max size
    if len(log) > MAX_ENCOUNTER_LOG_SIZE:
        log = log[:MAX_ENCOUNTER_LOG_SIZE]
    
    save_encounter_log(log)


def get_recent_encounters(count: int = 20) -> List[Dict[str, Any]]:
    """Get the most recent N encounters."""
    log = load_encounter_log()
    return log[:count]


def get_encounter_stats() -> Dict[str, Any]:
    """Get summary statistics from the encounter log."""
    log = load_encounter_log()
    
    if not log:
        return {
            "total_encounters": 0,
            "caught": 0,
            "defeated": 0,
            "fled": 0,
            "lost": 0,
            "shinies_encountered": 0,
            "catch_rate": 0.0,
        }
    
    total = len(log)
    caught = sum(1 for e in log if e.get("outcome") == "caught")
    defeated = sum(1 for e in log if e.get("outcome") == "defeated")
    fled = sum(1 for e in log if e.get("outcome") == "fled")
    lost = sum(1 for e in log if e.get("outcome") == "lost")
    shinies = sum(1 for e in log if e.get("shiny", False))
    
    return {
        "total_encounters": total,
        "caught": caught,
        "defeated": defeated,
        "fled": fled,
        "lost": lost,
        "shinies_encountered": shinies,
        "catch_rate": (caught / total * 100) if total > 0 else 0.0,
    }


def clear_encounter_log() -> None:
    """Clear the entire encounter log."""
    save_encounter_log([])


# --- Individual Pokemon Battle Stats Functions ---

def update_pokemon_battle_stats(individual_id: str, won: bool) -> bool:
    """
    Update the battle stats (wins/losses) for a specific Pokemon.
    
    Args:
        individual_id: The unique individual_id of the Pokemon
        won: True if the battle was won, False if lost
        
    Returns:
        True if the update was successful, False otherwise
    """
    try:
        if not mypokemon_path.is_file():
            return False
            
        with open(mypokemon_path, "r", encoding="utf-8") as f:
            pokemon_data = json.load(f)
        
        updated = False
        for pokemon in pokemon_data:
            if pokemon.get("individual_id") == individual_id:
                # Initialize stats if they don't exist
                if "battles_won" not in pokemon:
                    pokemon["battles_won"] = 0
                if "battles_lost" not in pokemon:
                    pokemon["battles_lost"] = 0
                
                # Update the appropriate stat
                if won:
                    pokemon["battles_won"] += 1
                else:
                    pokemon["battles_lost"] += 1
                
                updated = True
                break
        
        if updated:
            with open(mypokemon_path, "w", encoding="utf-8") as f:
                json.dump(pokemon_data, f, indent=2)
            return True
            
    except Exception as e:
        print(f"Ankimon: Error updating Pokemon battle stats: {e}")
    
    return False


def get_pokemon_battle_stats(individual_id: str) -> Dict[str, int]:
    """
    Get the battle stats for a specific Pokemon.
    
    Args:
        individual_id: The unique individual_id of the Pokemon
        
    Returns:
        Dictionary with battles_won and battles_lost counts
    """
    try:
        if not mypokemon_path.is_file():
            return {"battles_won": 0, "battles_lost": 0}
            
        with open(mypokemon_path, "r", encoding="utf-8") as f:
            pokemon_data = json.load(f)
        
        for pokemon in pokemon_data:
            if pokemon.get("individual_id") == individual_id:
                return {
                    "battles_won": pokemon.get("battles_won", 0),
                    "battles_lost": pokemon.get("battles_lost", 0),
                }
                
    except Exception as e:
        print(f"Ankimon: Error getting Pokemon battle stats: {e}")
    
    return {"battles_won": 0, "battles_lost": 0}


def get_top_battlers(count: int = 10) -> List[Dict[str, Any]]:
    """
    Get the top Pokemon by total battles or win rate.
    
    Args:
        count: Number of top battlers to return
        
    Returns:
        List of Pokemon with their battle stats, sorted by wins
    """
    try:
        if not mypokemon_path.is_file():
            return []
            
        with open(mypokemon_path, "r", encoding="utf-8") as f:
            pokemon_data = json.load(f)
        
        # Filter Pokemon with battle stats and calculate totals
        battlers = []
        for pokemon in pokemon_data:
            wins = pokemon.get("battles_won", 0)
            losses = pokemon.get("battles_lost", 0)
            total = wins + losses
            
            if total > 0:  # Only include Pokemon that have battled
                win_rate = (wins / total * 100) if total > 0 else 0
                battlers.append({
                    "name": pokemon.get("name", "Unknown"),
                    "nickname": pokemon.get("nickname", ""),
                    "individual_id": pokemon.get("individual_id"),
                    "id": pokemon.get("id"),
                    "level": pokemon.get("level", 1),
                    "battles_won": wins,
                    "battles_lost": losses,
                    "total_battles": total,
                    "win_rate": round(win_rate, 1),
                })
        
        # Sort by wins descending
        battlers.sort(key=lambda x: x["battles_won"], reverse=True)
        
        return battlers[:count]
        
    except Exception as e:
        print(f"Ankimon: Error getting top battlers: {e}")
    
    return []
