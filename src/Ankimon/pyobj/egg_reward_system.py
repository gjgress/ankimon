"""
Egg Reward System for Ankimon.

This module handles the automatic awarding of eggs to users who consistently use Ankimon.
Users receive a random egg every 3 days of active usage.

The system tracks:
- Last egg award date
- Consecutive usage days
- Total eggs awarded

Usage tracking is based on actual Ankimon usage (reviews during sessions), 
not just login days.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List

from aqt import mw
from aqt.utils import showInfo, tooltip

from ..resources import eggs_path, user_path, pokedex_path


# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

EGG_REWARD_FILE = user_path / "egg_reward_data.json"
DAYS_REQUIRED_FOR_EGG = 3  # Number of consecutive usage days to earn an egg

# Egg types and their Pokemon pools (pokemon_id ranges or specific IDs)
# Each type has a weight for random selection
EGG_TYPE_POOLS: Dict[str, Dict[str, Any]] = {
    "normal": {
        "pokemon_ids": [16, 19, 21, 52, 133, 161, 163, 174, 276, 293, 396, 399, 504, 519, 659, 731, 819],
        "weight": 25,
        "cards_required_range": (60, 100),
    },
    "fire": {
        "pokemon_ids": [4, 37, 58, 77, 126, 155, 218, 228, 255, 322, 390, 498, 513, 653, 725, 757, 813],
        "weight": 10,
        "cards_required_range": (80, 120),
    },
    "water": {
        "pokemon_ids": [7, 54, 60, 72, 86, 116, 129, 158, 183, 258, 270, 278, 341, 393, 501, 515, 656, 728, 816],
        "weight": 12,
        "cards_required_range": (80, 120),
    },
    "grass": {
        "pokemon_ids": [1, 43, 69, 102, 114, 152, 187, 252, 273, 315, 387, 420, 495, 511, 546, 650, 722, 810],
        "weight": 12,
        "cards_required_range": (80, 120),
    },
    "electric": {
        "pokemon_ids": [25, 81, 100, 125, 172, 179, 239, 309, 403, 417, 522, 587, 602, 694, 702, 737],
        "weight": 10,
        "cards_required_range": (80, 120),
    },
    "ice": {
        "pokemon_ids": [86, 124, 144, 215, 220, 238, 361, 459, 478, 582, 613, 712, 872, 875],
        "weight": 6,
        "cards_required_range": (100, 140),
    },
    "fighting": {
        "pokemon_ids": [56, 66, 106, 107, 236, 296, 307, 447, 532, 538, 539, 619, 674, 701, 759, 852],
        "weight": 8,
        "cards_required_range": (90, 130),
    },
    "poison": {
        "pokemon_ids": [23, 29, 32, 41, 48, 88, 109, 167, 316, 434, 451, 543, 568, 690, 747, 848],
        "weight": 8,
        "cards_required_range": (80, 120),
    },
    "ground": {
        "pokemon_ids": [27, 50, 74, 104, 111, 194, 207, 231, 328, 343, 449, 529, 551, 622, 749],
        "weight": 8,
        "cards_required_range": (80, 120),
    },
    "flying": {
        "pokemon_ids": [16, 21, 83, 84, 163, 176, 198, 276, 333, 396, 441, 519, 527, 580, 627, 661, 714, 731, 821],
        "weight": 10,
        "cards_required_range": (80, 120),
    },
    "psychic": {
        "pokemon_ids": [63, 79, 96, 102, 177, 280, 325, 343, 360, 436, 517, 561, 574, 605, 677, 765],
        "weight": 7,
        "cards_required_range": (100, 140),
    },
    "bug": {
        "pokemon_ids": [10, 13, 46, 48, 165, 167, 193, 204, 265, 290, 313, 314, 347, 401, 415, 540, 588, 616, 664, 736, 824],
        "weight": 12,
        "cards_required_range": (50, 80),
    },
    "rock": {
        "pokemon_ids": [74, 95, 138, 140, 142, 185, 246, 299, 345, 347, 369, 408, 410, 524, 564, 566, 688, 696, 698, 744, 837],
        "weight": 8,
        "cards_required_range": (90, 130),
    },
    "ghost": {
        "pokemon_ids": [92, 200, 353, 355, 425, 442, 562, 592, 607, 679, 708, 710, 778, 854, 864],
        "weight": 6,
        "cards_required_range": (100, 150),
    },
    "dragon": {
        "pokemon_ids": [147, 329, 371, 443, 610, 633, 704, 714, 782, 840, 885],
        "weight": 3,
        "cards_required_range": (120, 180),
    },
    "dark": {
        "pokemon_ids": [198, 215, 228, 261, 302, 318, 359, 434, 509, 551, 570, 624, 629, 633, 658, 686, 717, 827, 859],
        "weight": 6,
        "cards_required_range": (100, 140),
    },
    "steel": {
        "pokemon_ids": [81, 304, 374, 436, 599, 624, 679, 707, 777, 837, 878],
        "weight": 5,
        "cards_required_range": (110, 160),
    },
    "fairy": {
        "pokemon_ids": [35, 39, 173, 174, 175, 183, 209, 280, 303, 546, 669, 682, 684, 702, 755, 764, 778, 856, 868],
        "weight": 7,
        "cards_required_range": (90, 130),
    },
}


# ─────────────────────────────────────────────────────────────────────────────
# Data Persistence
# ─────────────────────────────────────────────────────────────────────────────

def load_egg_reward_data() -> Dict[str, Any]:
    """
    Load the egg reward tracking data from file.
    
    Returns:
        Dict containing:
            - last_usage_date: Last date the user used Ankimon (str, YYYY-MM-DD)
            - consecutive_days: Number of consecutive usage days (int)
            - last_egg_award_date: Date of last egg award (str, YYYY-MM-DD or None)
            - total_eggs_awarded: Total number of eggs awarded (int)
            - usage_history: List of recent usage dates (list of str)
    """
    default_data = {
        "last_usage_date": None,
        "consecutive_days": 0,
        "last_egg_award_date": None,
        "total_eggs_awarded": 0,
        "usage_history": [],
    }
    
    try:
        if EGG_REWARD_FILE.exists():
            with open(EGG_REWARD_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Ensure all keys exist
                for key, default_value in default_data.items():
                    if key not in data:
                        data[key] = default_value
                return data
    except (json.JSONDecodeError, IOError) as e:
        pass  # Return default data on error
    
    return default_data


def save_egg_reward_data(data: Dict[str, Any]) -> bool:
    """
    Save the egg reward tracking data to file.
    
    Args:
        data: Dictionary containing egg reward tracking data
        
    Returns:
        bool: True if save succeeded, False otherwise
    """
    try:
        with open(EGG_REWARD_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


# ─────────────────────────────────────────────────────────────────────────────
# Egg Generation
# ─────────────────────────────────────────────────────────────────────────────

def get_pokemon_name_by_id(pokemon_id: int) -> str:
    """
    Get the Pokemon name from the pokedex by ID.
    
    Args:
        pokemon_id: The Pokemon's national dex number
        
    Returns:
        str: Pokemon name (capitalized) or "Unknown" if not found
    """
    try:
        with open(pokedex_path, "r", encoding="utf-8") as f:
            pokedex = json.load(f)
            for pokemon in pokedex:
                if pokemon.get("id") == pokemon_id:
                    return pokemon.get("name", "Unknown").capitalize()
    except (json.JSONDecodeError, IOError, KeyError):
        pass
    
    # Fallback: return "Pokemon #ID"
    return f"Pokemon #{pokemon_id}"


def select_random_egg_type() -> str:
    """
    Select a random egg type based on weighted probabilities.
    
    Returns:
        str: The selected egg type (e.g., "fire", "water", etc.)
    """
    types = list(EGG_TYPE_POOLS.keys())
    weights = [EGG_TYPE_POOLS[t]["weight"] for t in types]
    
    return random.choices(types, weights=weights, k=1)[0]


def generate_random_egg(bonus_for_streak: int = 0) -> Dict[str, Any]:
    """
    Generate a random egg with a Pokemon inside.
    
    Args:
        bonus_for_streak: Bonus days of streak (reduces cards_required slightly)
        
    Returns:
        Dict containing:
            - id: Unique egg ID
            - pokemon_name: Name of the Pokemon inside
            - pokemon_id: National dex ID of the Pokemon
            - cards_done: 0 (just received)
            - cards_required: Number of cards needed to hatch
            - received_date: Today's date
            - egg_type: Type of egg (fire, water, etc.)
            - favorite: False
            - is_reward_egg: True (marks this as a reward egg)
    """
    # Select random type
    egg_type = select_random_egg_type()
    type_pool = EGG_TYPE_POOLS[egg_type]
    
    # Select random Pokemon from that type's pool
    pokemon_id = random.choice(type_pool["pokemon_ids"])
    pokemon_name = get_pokemon_name_by_id(pokemon_id)
    
    # Calculate cards required (with streak bonus reduction)
    min_cards, max_cards = type_pool["cards_required_range"]
    cards_required = random.randint(min_cards, max_cards)
    
    # Apply streak bonus (up to 20% reduction)
    streak_discount = min(bonus_for_streak * 2, 20)  # 2% per streak day, max 20%
    cards_required = int(cards_required * (100 - streak_discount) / 100)
    cards_required = max(cards_required, 30)  # Minimum 30 cards
    
    # Generate unique ID
    egg_id = f"reward_egg_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000, 9999)}"
    
    return {
        "id": egg_id,
        "pokemon_name": pokemon_name,
        "pokemon_id": pokemon_id,
        "cards_done": 0,
        "cards_required": cards_required,
        "received_date": datetime.now().strftime("%Y-%m-%d"),
        "egg_type": egg_type,
        "favorite": False,
        "is_reward_egg": True,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Egg Management
# ─────────────────────────────────────────────────────────────────────────────

def load_eggs() -> List[Dict[str, Any]]:
    """
    Load existing eggs from eggs.json.
    
    Returns:
        List of egg dictionaries
    """
    try:
        if eggs_path.exists():
            with open(eggs_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
    except (json.JSONDecodeError, IOError):
        pass
    return []


def save_eggs(eggs: List[Dict[str, Any]]) -> bool:
    """
    Save eggs to eggs.json.
    
    Args:
        eggs: List of egg dictionaries
        
    Returns:
        bool: True if save succeeded
    """
    try:
        with open(eggs_path, "w", encoding="utf-8") as f:
            json.dump(eggs, f, indent=2, ensure_ascii=False)
        return True
    except IOError:
        return False


def add_reward_egg(egg: Dict[str, Any]) -> bool:
    """
    Add a reward egg to the user's egg collection.
    
    Args:
        egg: Egg dictionary to add
        
    Returns:
        bool: True if successfully added
    """
    eggs = load_eggs()
    eggs.append(egg)
    return save_eggs(eggs)


# ─────────────────────────────────────────────────────────────────────────────
# Main Reward Logic
# ─────────────────────────────────────────────────────────────────────────────

def record_daily_usage() -> None:
    """
    Record that the user used Ankimon today.
    
    This should be called when the user completes at least one review.
    Updates the consecutive days counter and usage history.
    """
    data = load_egg_reward_data()
    today = datetime.now().strftime("%Y-%m-%d")
    
    # Check if already recorded today
    if data["last_usage_date"] == today:
        return  # Already recorded for today
    
    # Check if this continues a streak
    if data["last_usage_date"]:
        last_date = datetime.strptime(data["last_usage_date"], "%Y-%m-%d")
        today_date = datetime.strptime(today, "%Y-%m-%d")
        days_diff = (today_date - last_date).days
        
        if days_diff == 1:
            # Consecutive day!
            data["consecutive_days"] += 1
        elif days_diff > 1:
            # Streak broken
            data["consecutive_days"] = 1
        # days_diff == 0 shouldn't happen due to check above
    else:
        # First usage ever
        data["consecutive_days"] = 1
    
    data["last_usage_date"] = today
    
    # Update usage history (keep last 30 days)
    if today not in data["usage_history"]:
        data["usage_history"].append(today)
        data["usage_history"] = data["usage_history"][-30:]
    
    save_egg_reward_data(data)


def check_and_award_egg(logger=None, show_notification: bool = True) -> Optional[Dict[str, Any]]:
    """
    Check if the user has earned an egg reward and award it if so.
    
    Users earn an egg after DAYS_REQUIRED_FOR_EGG consecutive days of usage.
    After awarding, the consecutive days counter resets to 0.
    
    Args:
        logger: Optional logger for logging events
        show_notification: Whether to show a popup notification
        
    Returns:
        The awarded egg dict if an egg was awarded, None otherwise
    """
    data = load_egg_reward_data()
    
    # Check if user has enough consecutive days
    if data["consecutive_days"] < DAYS_REQUIRED_FOR_EGG:
        if logger:
            days_left = DAYS_REQUIRED_FOR_EGG - data["consecutive_days"]
            logger.log("info", f"Egg reward: {data['consecutive_days']}/{DAYS_REQUIRED_FOR_EGG} days. Need {days_left} more day(s).")
        return None
    
    # User has earned an egg!
    streak_bonus = data["consecutive_days"] - DAYS_REQUIRED_FOR_EGG  # Extra days beyond required
    egg = generate_random_egg(bonus_for_streak=streak_bonus)
    
    if add_reward_egg(egg):
        # Update tracking data
        data["last_egg_award_date"] = datetime.now().strftime("%Y-%m-%d")
        data["total_eggs_awarded"] = data.get("total_eggs_awarded", 0) + 1
        data["consecutive_days"] = 0  # Reset streak after award
        save_egg_reward_data(data)
        
        if logger:
            logger.log("info", f"Egg reward awarded! {egg['pokemon_name']} ({egg['egg_type']} type)")
        
        if show_notification:
            show_egg_reward_notification(egg, data["total_eggs_awarded"])
        
        return egg
    
    return None


def show_egg_reward_notification(egg: Dict[str, Any], total_eggs: int) -> None:
    """
    Show a notification popup for the egg reward.
    
    Args:
        egg: The awarded egg dictionary
        total_eggs: Total number of eggs the user has been awarded
    """
    message = f"""
Congratulations!

You've been using Ankimon consistently for {DAYS_REQUIRED_FOR_EGG} days!

As a reward, you received a mysterious egg:

[ {egg['egg_type'].upper()} TYPE EGG ]

A {egg['pokemon_name']} is waiting to hatch!
Requires {egg['cards_required']} card reviews to hatch.

Total eggs earned: {total_eggs}

Keep up the great work with your studies!
"""
    
    showInfo(message, title="Egg Reward!")


def get_egg_reward_status() -> Dict[str, Any]:
    """
    Get the current status of the egg reward system.
    
    Returns:
        Dict containing:
            - consecutive_days: Current streak
            - days_until_egg: Days needed until next egg
            - total_eggs_awarded: Total eggs awarded
            - last_usage_date: Last usage date
            - progress_percent: Percentage progress to next egg
    """
    data = load_egg_reward_data()
    
    consecutive = data.get("consecutive_days", 0)
    days_until = max(0, DAYS_REQUIRED_FOR_EGG - consecutive)
    progress = min(100, int((consecutive / DAYS_REQUIRED_FOR_EGG) * 100))
    
    return {
        "consecutive_days": consecutive,
        "days_until_egg": days_until,
        "total_eggs_awarded": data.get("total_eggs_awarded", 0),
        "last_usage_date": data.get("last_usage_date"),
        "progress_percent": progress,
    }


def show_egg_progress_tooltip() -> None:
    """
    Show a tooltip with the current egg reward progress.
    """
    status = get_egg_reward_status()
    
    if status["days_until_egg"] == 0:
        message = "You have an egg reward waiting! Complete a review to claim it."
    else:
        message = f"Egg progress: {status['consecutive_days']}/{DAYS_REQUIRED_FOR_EGG} days ({status['progress_percent']}%)"
        if status["days_until_egg"] == 1:
            message += "\nJust 1 more day to earn an egg!"
        else:
            message += f"\n{status['days_until_egg']} more days to earn an egg!"
    
    tooltip(message, period=3000)


# ─────────────────────────────────────────────────────────────────────────────
# Hook Integration
# ─────────────────────────────────────────────────────────────────────────────

_daily_usage_recorded = False

def on_review_completed(logger=None) -> None:
    """
    Called when a review is completed. Records daily usage and checks for egg reward.
    
    This function should be called once per review session (or on first review of the day).
    
    Args:
        logger: Optional logger for logging
    """
    global _daily_usage_recorded
    
    if not _daily_usage_recorded:
        record_daily_usage()
        _daily_usage_recorded = True
        
        # Check if user earned an egg
        check_and_award_egg(logger=logger, show_notification=True)


def reset_daily_flag() -> None:
    """
    Reset the daily usage flag. Should be called at the start of each session.
    """
    global _daily_usage_recorded
    _daily_usage_recorded = False


def check_egg_reward_on_startup(logger=None) -> None:
    """
    Check for pending egg rewards on startup.
    
    This handles the case where a user reached 3 days on their last session
    but didn't complete a review to trigger the award.
    
    Args:
        logger: Optional logger for logging
    """
    reset_daily_flag()
    
    data = load_egg_reward_data()
    
    if logger:
        status = get_egg_reward_status()
        logger.log("info", f"Egg reward system: {status['consecutive_days']}/{DAYS_REQUIRED_FOR_EGG} days progress")
    
    # If user has enough days, they'll get the egg on their first review
    if data.get("consecutive_days", 0) >= DAYS_REQUIRED_FOR_EGG:
        if logger:
            logger.log("info", "User has earned an egg! Will award on first review.")
