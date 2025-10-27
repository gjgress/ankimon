import sys
import json
from ..resources import user_path
import os
import uuid
import datetime

new_values = {
    "everstone": False,
    "shiny": False,
    "mega": False,
    "special-form": None,
    "friendship": 0,
    "pokemon_defeated": 0,
    "ability": "No Ability",
    "individual_id": uuid.uuid4(),
    "nickname": "",
    "base_experience": 50,
    "current_hp": 50,
    "growth_rate": "medium-slow",
    "gender": "N",
    "type": ["Normal"],
    "attacks": ["tackle", "growl"],
    "evos": [],
    "id": 132,
    "captured_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
}

class DataHandler:
    """A class for managing the user's data files in the Ankimon addon.

    This class is a critical component of the addon's data management system.
    It is responsible for reading, validating, and updating the user's data
    files, ensuring that the data is always in a consistent and usable state.
    This includes assigning unique IDs to Pokémon, adding new data fields as
    the addon evolves, and saving the updated data back to the files.
    """
    def __init__(self):
        """Initializes the DataHandler and reads the user's data files."""
        self.new_values = new_values
        self.path = user_path  # Store the provided path
        self.data = {}         # Store any potential errors or file read issues
        self.read_files()

    def read_files(self):
        """Reads all of the user's data files.

        This method iterates through a list of predefined data files, reads
        their contents, and stores them as attributes of the `DataHandler`
        instance. It also creates the files with default content if they do
        not exist, ensuring that the addon can always function, even on a
        fresh installation.
        """
        # Specify the files to read
        files = ['mypokemon.json', 'mainpokemon.json', 'items.json', 'team.json', 'data.json', 'badges.json']

        # Loop through each file and attempt to read it from the specified path

        for file in files:
            file_path = os.path.join(self.path, file)  # Construct full file path
            attr_name = os.path.splitext(file)[0]      # Use the filename without extension as the attribute name

            # Create file with empty array if it doesn't exist
            if not os.path.exists(file_path):
                os.makedirs(os.path.dirname(file_path), exist_ok=True)  # Ensure directory exists
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, indent=2)

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = json.load(f)

                    # Validate list structure
                    if attr_name in ['mypokemon', 'mainpokemon'] and isinstance(content, list):
                        valid_content = []
                        for entry in content:
                            if isinstance(entry, dict):
                                valid_content.append(entry)
                            else:
                                print(f"Skipping invalid entry in {file}: {entry}")
                        setattr(self, attr_name, valid_content)
                    else:
                        setattr(self, attr_name, content)
            except Exception as e:
                self.data[file] = f"Error reading {file}: {e}"

    def assign_unique_ids(self, pokemon_list):
        """Assigns a unique 'individual_id' to each Pokémon in a list.

        This method ensures that every Pokémon has a unique identifier, which
        is crucial for tracking individual Pokémon and their progress. It only
        assigns an ID if one is not already present, preserving existing data.

        Args:
            pokemon_list (list): A list of Pokémon dictionaries.

        Raises:
            ValueError: If the input is not a list of dictionaries.
        """
        if not isinstance(pokemon_list, list):
            raise ValueError("Expected list of Pokémon dictionaries")

        unique_ids = set()
        for idx, entry in enumerate(pokemon_list):
            if not isinstance(entry, dict):
                print(f"Skipping invalid entry at index {idx} - not a dictionary")
                continue
        try:
            unique_ids = set(pokemon.get("individual_id") for pokemon in pokemon_list if "individual_id" in pokemon)

            for pokemon in pokemon_list:
                # Skip Pokémon that already have an individual_id
                if "individual_id" in pokemon and pokemon["individual_id"]:
                    unique_ids.add(pokemon["individual_id"])  # Ensure existing IDs are tracked
                    continue

                # Assign a new unique ID
                while True:
                    new_id = str(uuid.uuid4())
                    if new_id not in unique_ids:
                        pokemon["individual_id"] = new_id
                        unique_ids.add(new_id)
                        break
        except:
            print("Unique ID assignment failed")

    def assign_new_variables(self, pokemon_list):
        """Adds new data fields to each Pokémon in a list.

        This method is used to update the data structure of Pokémon as new
        features are added to the addon. It adds new fields with default
        values, ensuring that the data is always compatible with the latest
        version of the addon.

        Args:
            pokemon_list (list): A list of Pokémon dictionaries.
        """
        for pokemon in pokemon_list:
            for field, default_value in self.new_values.items():
                if field not in pokemon:  # Check if the field is not already set
                    pokemon[field] = default_value

    def save_file(self, attr_name):
        """Saves the updated data back to its respective JSON file.

        Args:
            attr_name (str): The name of the attribute to be saved, which
                             corresponds to the filename.
        """
        if hasattr(self, attr_name):
            file_path = os.path.join(self.path, f"{attr_name}.json")
            try:
                with open(file_path, 'w') as f:
                    json.dump(getattr(self, attr_name), f, indent=2)
            except Exception as e:
                self.data[file_path] = f"Error saving {file_path}: {e}"
