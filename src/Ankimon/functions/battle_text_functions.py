def effectiveness_text(effect_value):
    """Generates a descriptive text for the effectiveness of a Pokémon's attack.

    This function is a key part of the battle system, providing clear and
    concise feedback to the user about the outcome of each move. It translates
    the numerical effectiveness value into a human-readable string, which is
    then displayed in the battle log.

    Args:
        effect_value (float): The numerical effectiveness of the attack.

    Returns:
        str: A descriptive string (e.g., "was super effective !").
    """
    if effect_value == 0:
        effective_txt = "has missed."
    elif effect_value <= 0.5:
        effective_txt = "was not very effective."
    elif effect_value <= 1:
        effective_txt = "was effective."
    elif effect_value <= 1.5:
        effective_txt = "was very effective !"
    elif effect_value <= 2:
        effective_txt = "was super effective !"
    else:
        effective_txt = "was effective."
        #return None
    return effective_txt