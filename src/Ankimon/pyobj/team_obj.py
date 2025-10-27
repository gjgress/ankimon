from ..resources import team_json_path
from aqt import mw
from aqt.utils import tooltip
import json
from .pokemon_obj import PokemonObject, PokemonEncoder

class TeamPokemonObject:
    """Manages the player's team of up to six Pokémon.

    This class is responsible for handling the player's Pokémon team,
    including adding, removing, and trading Pokémon. It also provides methods
    for saving and loading the team's state to and from a JSON file, ensuring
    data persistence between sessions.
    """
    def __init__(self, pokemon_1=None, pokemon_2=None, pokemon_3=None, pokemon_4=None, pokemon_5=None, pokemon_6=None):
        """Initializes the Pokémon team with up to six members.

        Args:
            pokemon_1 (PokemonObject, optional): The Pokémon in the first slot.
            pokemon_2 (PokemonObject, optional): The Pokémon in the second slot.
            pokemon_3 (PokemonObject, optional): The Pokémon in the third slot.
            pokemon_4 (PokemonObject, optional): The Pokémon in the fourth slot.
            pokemon_5 (PokemonObject, optional): The Pokémon in the fifth slot.
            pokemon_6 (PokemonObject, optional): The Pokémon in the sixth slot.
        """
        self.save_directory = team_json_path
        self.pokemon_1 = pokemon_1
        self.pokemon_2 = pokemon_2
        self.pokemon_3 = pokemon_3
        self.pokemon_4 = pokemon_4
        self.pokemon_5 = pokemon_5
        self.pokemon_6 = pokemon_6

    def trade_pokemon(self, team_position, PokemonObject):
        """Swaps a Pokémon in a specified team slot with a new one.

        This method updates the team composition, refreshes the Anki deck
        browser to reflect the change, and then saves the updated team to the
        JSON file.

        Args:
            team_position (int): The slot in the team to be updated (1-6).
            PokemonObject (PokemonObject): The new Pokémon to be placed in the slot.

        Raises:
            ValueError: If the provided team_position is not between 1 and 6.
        """
        if team_position not in {1, 2, 3, 4, 5, 6}:
            raise ValueError("Invalid team position, must be 1 through 6")
        # Use setattr to dynamically set the attribute based on team_position
        setattr(self, f"pokemon_{team_position}", PokemonObject)
        mw.deckBrowser.refresh()
        tooltip(f"Pokemon {team_position} has been successfully switched out with {PokemonObject.name}.")
        self.save_team()
        #if team_position == 1:
        #    MainPokemonObject = pokemon_1

    def save_team(self):
        """Saves the current team composition to a JSON file.

        This method serializes the `TeamPokemonObject` into a JSON format,
        ensuring that the player's team is preserved between Anki sessions. It
        uses a custom JSON encoder to handle the `PokemonObject` instances.
        """
        team_pokemon_dict = {
            "pokemon_1": self.pokemon_1,
            "pokemon_2": self.pokemon_2,
            "pokemon_3": self.pokemon_3,
            "pokemon_4": self.pokemon_4,
            "pokemon_5": self.pokemon_5,
            "pokemon_6": self.pokemon_6
        }
        # Serialize PokemonObject instances using custom encoder
        serialized_team = {}
        for key, value in team_pokemon_dict.items():
            if isinstance(value, PokemonObject):
                serialized_team[key] = value

        with open(self.save_directory, "w") as file:
            json.dump(serialized_team, file, indent=4, cls=PokemonEncoder)
