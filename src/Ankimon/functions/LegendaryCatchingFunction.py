class LegendaryCatching:
    """Manages the complex logic of legendary Pokémon encounters.

    This class is a key part of the addon's endgame content, providing a
    challenging and rewarding experience for dedicated players. It enforces a
    set of rules and dependencies, ensuring that legendary Pokémon can only be
    caught in a specific order.
    """
    def __init__(self):
        """Initializes the legendary catching rules and dependencies."""
        # Define dependencies
        self.dependencies = {
            150: {151},  # Mewtwo requires Mew
            250: {243, 244, 245},  # Ho-Oh requires Raikou, Entei, Suicune
            249: {243, 244, 245},  # Lugia requires Raikou, Entei, Suicune
            486: {377, 378, 379},  # Regigigas requires Regirock, Regice, Registeel
            384: {382, 383},  # Rayquaza requires Kyogre and Groudon
            487: {483, 484},  # Giratina requires Dialga and Palkia
        }

        # Define mythical Pokémon (always excluded)
        self.mythical = {151, 251, 386, 493, 649}

        # List of Pokémon initially excluded
        self.excluded = {
            144, 145, 146, 150, 243, 244, 245, 250, 249,
            377, 378, 379, 486, 380, 381, 382, 383, 384,
            483, 484, 487
        }

    def can_catch(self, caught_pokemon, target_pokemon):
        """Checks if a legendary Pokémon can be caught.

        This method determines if the user has met the necessary prerequisites
        to encounter and catch a specific legendary Pokémon.

        Args:
            caught_pokemon (set): A set of the Pokémon IDs that the user has
                                  already caught.
            target_pokemon (int): The ID of the legendary Pokémon to check.

        Returns:
            bool: True if the Pokémon can be caught, False otherwise.
        """
        if target_pokemon in self.mythical:
            return False  # Mythical Pokémon cannot be caught

        if target_pokemon not in self.dependencies:
            return True  # Pokémon has no dependency, can be caught

        required = self.dependencies[target_pokemon]
        return required.issubset(caught_pokemon)

    def get_catchable_pokemon(self, caught_pokemon):
        """Returns a set of all legendary Pokémon that are currently catchable.

        This method is used to determine which legendary Pokémon can be
        encountered, based on the user's current collection.

        Args:
            caught_pokemon (set): A set of the Pokémon IDs that the user has
                                  already caught.

        Returns:
            set: A set of the Pokémon IDs that are currently catchable.
        """
        catchable = set()
        for pokemon in self.excluded:
            if self.can_catch(caught_pokemon, pokemon):
                catchable.add(pokemon)
        return catchable


# Example usage
caught = {151, 243, 244, 245}  # Already caught Mew, Raikou, Entei, Suicune
catching = LegendaryCatching()

print("Catchable Pokémon:", catching.get_catchable_pokemon(caught))
