import json
from typing import Optional

from ..functions.pokedex_functions import search_pokedex, search_pokedex_by_id
from ..resources import mainpokemon_path
from ..pyobj.pokemon_obj import PokemonObject

# default values to fall back in case of load error
MAIN_POKEMON_DEFAULT = {
    "name": "RESTART ANKI",
    "gender": "M",
    "level": 5,
    "id": 0,
    "ability": "Static",
    "type": ["Electric"],
    "base_stats": {
        "hp": 20,
        "atk": 30,
        "def": 15,
        "spa": 50,
        "spd": 40,
        "spe": 60,
    },
    "xp": 0,
    "ev": {
        "hp": 0,
        "atk": 1,
        "def": 0,
        "spa": 0,
        "spd": 0,
        "spe": 0
    },
    "iv": {
        "hp": 15,
        "atk": 20,
        "def": 10,
        "spa": 10,
        "spd": 10,
        "spe": 10
    },
    "attacks": [
        "Thunderbolt",
        "Quick Attack"
    ],
    "base_experience": 112,
    "hp": 20,
    "growth_rate": "medium",
    "evos": ["Pikachu"]
}


def update_main_pokemon(main_pokemon: Optional[PokemonObject] = None):
    """Updates or initializes the main Pokémon object from a JSON file.

    This function is a cornerstone of the addon's data management, responsible
    for ensuring that the user's main Pokémon is always up-to-date. It reads
    the Pokémon's data from `mainpokemon.json`, updates the provided
    `PokemonObject` with the latest stats, and handles cases where the file is
    missing or corrupted by falling back to a default Pokémon.

    Args:
        main_pokemon (PokemonObject, optional): The `PokemonObject` to be
            updated. If not provided, a new one is created.

    Returns:
        tuple: A tuple containing the updated or new `PokemonObject` and a
               boolean indicating if the data was loaded from a file (False)
               or if a default was used (True).
    """

    if main_pokemon is None:
        main_pokemon = PokemonObject(**MAIN_POKEMON_DEFAULT)

    mainpokemon_empty = True
    if mainpokemon_path.is_file():
        with open(mainpokemon_path, "r", encoding="utf-8") as mainpokemon_json:
            try:
                main_pokemon_data = json.load(mainpokemon_json)
                # if main pokemon is successfully loaded make empty false
                if main_pokemon_data:
                    mainpokemon_empty = False
                    pokemon_name = search_pokedex_by_id(main_pokemon_data[0]["id"])
                    main_pokemon_data[0]["base_stats"] = search_pokedex(pokemon_name, "baseStats")
                    del main_pokemon_data[0]["stats"]  # For legacy code, i.e. for when "stats" in the JSON actually meant "base_stat"
                    main_pokemon.update_stats(**main_pokemon_data[0])
                    save_main_pokemon(main_pokemon) # Save the updated main Pokémon data
                # if file does load or is empty use default value
                else:
                    main_pokemon = PokemonObject(**MAIN_POKEMON_DEFAULT)
                max_hp = main_pokemon.calculate_max_hp()
                main_pokemon.max_hp = max_hp
                if main_pokemon_data[0].get("current_hp", max_hp) > max_hp:
                    main_pokemon_data[0]["current_hp"] = max_hp
                if main_pokemon_data:
                    main_pokemon.hp = main_pokemon_data[0].get("current_hp", max_hp)
                return main_pokemon, mainpokemon_empty


            except Exception as e:
                main_pokemon = PokemonObject(**MAIN_POKEMON_DEFAULT)
                return main_pokemon, mainpokemon_empty
    else:
        return PokemonObject(**MAIN_POKEMON_DEFAULT), mainpokemon_empty

def save_main_pokemon(main_pokemon: PokemonObject):
    """
    Saves the main Pokémon object to the mainpokemon.json file.
    Args:
        main_pokemon (PokemonObject): The Pokémon object to save.
    """
    # If the object has a to_dict method, use it; otherwise, use __dict__
    if hasattr(main_pokemon, 'to_dict'):
        data = main_pokemon.to_dict()
    else:
        data = main_pokemon.__dict__
    # Write as a single-element list for compatibility
    with open(mainpokemon_path, "w", encoding="utf-8") as f:
        json.dump([data], f, indent=4)


