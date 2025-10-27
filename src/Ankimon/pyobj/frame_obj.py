class FrameObject:
    """A data class for managing the state of the battle interface.

    This class encapsulates all the necessary information to render a single
    frame of a Pokémon battle, including the battle text, the Pokémon involved,
    and any visual effects.
    """
    def __init__(self, text, main_pokemon, enemy_pokemon):
        """Initializes a FrameObject with the current battle state.

        Args:
            text (str): The message to be displayed in the battle log.
            main_pokemon (dict): A dictionary representing the player's Pokémon.
            enemy_pokemon (dict): A dictionary representing the opponent's Pokémon.
        """
        self.text = text
        self.display = "block"
        self.main_pokemon = main_pokemon
        self.enemy_pokemon = enemy_pokemon
        self.mainpokemon_attack = False
        self.enemypokemon_attack = False
        self.fx_top = None
        self.fx_bottom = None