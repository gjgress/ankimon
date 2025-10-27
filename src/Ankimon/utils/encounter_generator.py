import random, json
from resources import all_species_path, pokemon_species_normal_path, pokemon_species_baby_path, pokemon_species_ultra_path, pokemon_species_lengendary_path, pokemon_species_mythical_path

def get_pokemon_id_by_tier(tier):
    """Selects a random Pokémon ID from a specified tier.

    This function is a core component of the encounter generation system,
    responsible for selecting a random Pokémon from a given rarity tier. It
    reads the appropriate JSON file for the tier and returns a random ID from
    that list.

    Args:
        tier (str): The rarity tier of the Pokémon (e.g., 'Normal', 'Baby').

    Returns:
        tuple: A tuple containing the randomly selected Pokémon ID and the
               name of the tier.
    """
    id_species_path = None
    if tier == "Normal":
        id_species_path = pokemon_species_normal_path
    elif tier == "Baby":
        id_species_path = pokemon_species_baby_path
    elif tier == "Ultra":
        id_species_path = pokemon_species_ultra_path
    elif tier == "Legendary":
        id_species_path = pokemon_species_legendary_path
    elif tier == "Mythical":
        id_species_path = pokemon_species_mythical_path

    with open(id_species_path, 'r') as file:
        id_data = json.load(file)

    pokemon_species = f"{tier}"
    # Select a random Pokemon ID from those in the tier
    random_pokemon_id = random.choice(id_data)
    return random_pokemon_id, pokemon_species

def get_tier(card_counter, cards_per_round, player_level=None, event_modifier=None):
    """Determines the rarity tier of a Pokémon encounter.

    This function calculates the probabilities of encountering Pokémon from
    different rarity tiers based on the number of cards reviewed, the player's
    level, and any active event modifiers. It then returns a randomly selected
    tier based on these probabilities.

    Args:
        card_counter (int): The total number of cards reviewed.
        cards_per_round (int): The number of cards in a review round.
        player_level (int, optional): The player's current level.
        event_modifier (float, optional): A multiplier for event-based
                                          adjustments.

    Returns:
        str: The name of the selected rarity tier.
    """
    percentages = get_base_percentages(card_counter, cards_per_round)
    percentages = modify_percentages(percentages, player_level, event_modifier)

    tiers = list(percentages.keys())
    probabilities = list(percentages.values())

    choice = random.choices(tiers, probabilities, k=1)
    return choice[0]

def calculate_percentages(card_counter, cards_per_round, player_level=None, event_modifier=None):
    """Calculates the encounter rate percentages for each rarity tier.

    This function is a utility for displaying the current encounter rates to
    the user, providing transparency into the addon's mechanics.

    Args:
        card_counter (int): The total number of cards reviewed.
        cards_per_round (int): The number of cards in a review round.
        player_level (int, optional): The player's current level.
        event_modifier (float, optional): A multiplier for event-based
                                          adjustments.

    Returns:
        dict: A dictionary of the encounter rate percentages for each tier.
    """
    percentages = get_base_percentages(card_counter, cards_per_round)
    percentages = modify_percentages(percentages, player_level, event_modifier)
    return percentages

def get_pokemon_by_category(category_name):
    """Selects a random Pokémon name from a specified category.

    Args:
        category_name (str): The name of the Pokémon category (e.g., 'Normal').

    Returns:
        str: The name of the randomly selected Pokémon.
    """
    # Reload the JSON data from the file
    global all_species_path
    with open(all_species_path, 'r') as file:
        pokemon_data = json.load(file)
    # Convert the input to lowercase to match the values in our JSON data
    category_name = category_name.lower()

    # Filter the Pokémon data to only include those in the given tier
    pokemon_in_tier = [pokemon['name'] for pokemon in pokemon_data if pokemon['Tier'].lower() == category_name]
    random_pokemon_name_from_tier = f"{(random.choice(pokemon_in_tier)).lower()}"
    random_pokemon_name_from_tier = special_pokemon_names_for_min_level(random_pokemon_name_from_tier)
    return random_pokemon_name_from_tier #return random pokemon name from that category

def get_base_percentages(card_counter, cards_per_round):
    """Returns the base encounter rate percentages for each rarity tier.

    These base rates are determined by the number of cards reviewed, and are
    then modified by other factors such as player level and events.

    Args:
        card_counter (int): The total number of cards reviewed.
        cards_per_round (int): The number of cards in a review round.

    Returns:
        dict: A dictionary of the base encounter rate percentages.
    """
    if card_counter < (40 * cards_per_round):
        return {"Normal": 100}
    elif card_counter < (50 * cards_per_round):
        return {"Baby": 12.5, "Normal": 87.5}
    elif card_counter < (65 * cards_per_round):
        return {"Baby": 11.1, "Normal": 77.8, "Ultra": 11.1}
    elif card_counter < (90 * cards_per_round):
        return {"Baby": 10, "Legendary": 10, "Normal": 70, "Ultra": 20}
    else:
        return {"Baby": 8.33, "Legendary": 8.33, "Mythical": 8.33, "Normal": 58.34, "Ultra": 16.67}

def modify_percentages(percentages, player_level=None, event_modifier=None):
    """Modifies the encounter rate percentages based on various factors.

    This function adjusts the base encounter rates based on the player's level
    and any active event modifiers, adding a layer of dynamic complexity to the
    encounter system.

    Args:
        percentages (dict): The base encounter rate percentages.
        player_level (int, optional): The player's current level.
        event_modifier (float, optional): A multiplier for event-based
                                          adjustments.

    Returns:
        dict: The modified encounter rate percentages.
    """
    # Example modification based on player level
    if player_level:
        adjustment = 5  # Adjustment value for the example
        if player_level > 10:
            for tier in percentages:
                if tier == "Normal":
                    percentages[tier] = max(percentages[tier] - adjustment, 0)
                else:
                    percentages[tier] = percentages.get(tier, 0) + adjustment

    # Example modification based on special event
    if event_modifier:
        for tier in percentages:
            percentages[tier] *= event_modifier

    # Normalize percentages to ensure they sum to 100
    total = sum(percentages.values())
    for tier in percentages:
        percentages[tier] = (percentages[tier] / total) * 100

    return percentages

def special_pokemon_names_for_min_level(name):
    if name == "flabébé":
        return "flabebe"
    elif name == "sirfetch'd":
        return "sirfetchd"
    elif name == "farfetch'd":
        return "farfetchd"
    elif name == "porygon-z":
        return "porygonz"
    elif name == "kommo-o":
        return "kommoo"
    elif name == "hakamo-o":
        return "hakamoo"
    elif name == "jangmo-o":
        return "jangmoo"
    elif name == "mr. rime":
        return "mrrime"
    elif name == "mr. mime":
        return "mrmime"
    elif name == "mime jr.":
        return "mimejr"
    elif name == "nidoran♂":
        return "nidoranm"
    elif name == "nidoran":
        return "nidoranf"
    elif name == "keldeo[e]":
        return "keldeo"
    elif name == "mew[e]":
        return "mew"
    elif name == "deoxys[e]":
        return "deoxys"
    elif name == "jirachi[e]":
        return "jirachi"
    elif name == "arceus[e]":
        return "arceus"
    elif name == "shaymin[e]":
        return "shaymin-land"
    elif name == "darkrai [e]":
        return "darkrai"
    elif name == "manaphy[e]":
        return "manaphy"
    elif name == "phione[e]":
        return "phione"
    elif name == "celebi[e]":
        return "celebi"
    elif name == "magearna[e]":
        return "magearna"
    elif name == "type: null":
        return "typenull"
    else:
        #showWarning("Error in Handling Pokémon name")
        return name

def special_pokemon_names_for_pokedex_to_poke_api_db(name):
    global pokedex_to_poke_api_db
    return pokedex_to_poke_api_db.get(name, name)

def choose_random_pkmn_from_tier(cards_per_round, card_counter):
    possible_tiers = []
    try:
        percentages = calculate_percentages(card_counter, cards_per_round)
        tier = get_tier(card_counter, cards_per_round)
        id, pokemon_species = get_pokemon_id_by_tier(tier)
        return id, pokemon_species
    except:
        showWarning(f" An error occured with generating following Pkmn Info: {id}{pokemon_species} \n Please post this error message over the Report Bug Issue")