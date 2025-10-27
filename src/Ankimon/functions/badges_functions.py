import json

from ..resources import badgebag_path

def check_badges(achievements):
    """Synchronizes the achievements dictionary with the user's saved badges.

    This function reads the `badgebag.json` file, which contains a list of all
    the badges the user has earned, and updates the in-memory `achievements`
    dictionary to reflect this data. This ensures that the addon's state is
    always consistent with the saved data.

    Args:
        achievements (dict): The dictionary of achievements to be updated.

    Returns:
        dict: The updated achievements dictionary.
    """
    with open(badgebag_path, "r", encoding="utf-8") as json_file:
        badge_list = json.load(json_file)
        for badge_num in badge_list:
            achievements[str(badge_num)] = True
    return achievements

def check_for_badge(achievements, rec_badge_num):
    """Checks if a specific badge has been earned.

    This function first synchronizes the `achievements` dictionary with the
    saved data, then checks if the specified badge is marked as earned.

    Args:
        achievements (dict): The dictionary of achievements.
        rec_badge_num (int): The number of the badge to check.

    Returns:
        bool: True if the badge has been earned, False otherwise.
    """
    achievements = check_badges(achievements)
    if achievements[str(rec_badge_num)] is False:
        got_badge = False
    else:
        got_badge = True
    return got_badge

def save_badges(badges_collection):
    """Saves the user's earned badges to a JSON file.

    This function is responsible for persisting the user's badge collection,
    ensuring that their progress is not lost between sessions.

    Args:
        badges_collection (list): A list of the badge numbers that the user
                                  has earned.
    """
    with open(badgebag_path, 'w') as json_file:
        json.dump(badges_collection, json_file)

def receive_badge(badge_num,achievements):
    """Awards a new badge to the user.

    This function updates the `achievements` dictionary to mark the new badge
    as earned, then reconstructs the user's badge collection and saves it to
    the JSON file.

    Args:
        badge_num (int): The number of the badge to be awarded.
        achievements (dict): The dictionary of achievements.

    Returns:
        dict: The updated achievements dictionary.
    """
    achievements = check_badges(achievements)
    #for badges in badge_list:
    achievements[str(badge_num)] = True
    badges_collection = []
    for num in range(1,69):
        if achievements[str(num)] is True:
            badges_collection.append(int(num))
    save_badges(badges_collection)
    return achievements

def handle_achievements(card_counter, achievements):
    """Awards badges based on the number of cards reviewed.

    This function is a key part of the addon's progression system, rewarding
    users with badges as they reach certain milestones in their studies.

    Args:
        card_counter (int): The total number of cards reviewed.
        achievements (dict): The dictionary of achievements.

    Returns:
        dict: The updated achievements dictionary.
    """
    if card_counter == 100:
        check = check_for_badge(achievements,1)
        if check is False:
            achievements = receive_badge(1,achievements)
    elif card_counter == 200:
        check = check_for_badge(achievements,2)
        if check is False:
            achievements = receive_badge(2,achievements)
    elif card_counter == 300:
        check = check_for_badge(achievements,3)
        if check is False:
            achievements = receive_badge(3,achievements)
    elif card_counter == 500:
        check = check_for_badge(achievements,4)
        if check is False:
            receive_badge(4,achievements)
    return achievements

def check_and_award_badges(card_counter, achievements, ankimon_tracker_obj, test_window):
    """Checks for and awards item-related badges.

    This function is triggered when the user receives an item, and it awards a
    specific badge to commemorate the event.

    Args:
        card_counter (int): The total number of cards reviewed.
        achievements (dict): The dictionary of achievements.
        ankimon_tracker_obj: The addon's main tracker object.
        test_window: The main battle window object.

    Returns:
        dict: The updated achievements dictionary.
    """
    if card_counter == ankimon_tracker_obj.item_receive_value:
        test_window.display_item()
        check = check_for_badge(achievements,6)
        if check is False:
            receive_badge(6,achievements)
    return achievements