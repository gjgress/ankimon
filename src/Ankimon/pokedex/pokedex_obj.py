import os
import json
from aqt import QDialog, QVBoxLayout, QWebEngineView, mw
from PyQt6.QtCore import QUrlQuery, QObject, pyqtSlot
from PyQt6.QtWebChannel import QWebChannel
from aqt.qt import Qt, QFile, QUrl, QFrame, QPushButton
from aqt.utils import showInfo
from ..resources import mypokemon_path, pokedex_path, learnset_path, moves_file_path
from ..functions.pokedex_functions import (
    search_pokedex,
    search_pokedex_by_id,
    find_details_move,
)


class PokedexBridge(QObject):
    """Bridge class for JavaScript to Python communication in Pokedex."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._pokedex_data = None
        self._learnset_data = None
        self._moves_data = None
    
    def _load_pokedex(self):
        """Load pokedex data lazily."""
        if self._pokedex_data is None:
            try:
                with open(str(pokedex_path), "r", encoding="utf-8") as f:
                    self._pokedex_data = json.load(f)
            except Exception as e:
                print(f"Error loading pokedex: {e}")
                self._pokedex_data = {}
        return self._pokedex_data
    
    def _load_learnsets(self):
        """Load learnset data lazily."""
        if self._learnset_data is None:
            try:
                with open(str(learnset_path), "r", encoding="utf-8") as f:
                    self._learnset_data = json.load(f)
            except Exception as e:
                print(f"Error loading learnsets: {e}")
                self._learnset_data = {}
        return self._learnset_data
    
    def _load_moves(self):
        """Load moves data lazily."""
        if self._moves_data is None:
            try:
                with open(str(moves_file_path), "r", encoding="utf-8") as f:
                    self._moves_data = json.load(f)
            except Exception as e:
                print(f"Error loading moves: {e}")
                self._moves_data = {}
        return self._moves_data
    
    @pyqtSlot(int, result=str)
    def getPokemonDetails(self, pokemon_id):
        """Get Pokemon details including evolutions by ID."""
        try:
            # Use existing pokedex_functions to get pokemon name by ID
            pokemon_name = search_pokedex_by_id(pokemon_id)
            if not pokemon_name or pokemon_name == "Pokémon not found":
                return json.dumps({"error": "Pokemon not found"})
            
            # Get pokemon data using search_pokedex
            name = search_pokedex(pokemon_name, "name") or pokemon_name
            types = search_pokedex(pokemon_name, "types") or []
            base_stats = search_pokedex(pokemon_name, "baseStats") or {}
            abilities = search_pokedex(pokemon_name, "abilities") or {}
            evos = search_pokedex(pokemon_name, "evos") or []
            prevo_name = search_pokedex(pokemon_name, "prevo")
            evo_level = search_pokedex(pokemon_name, "evoLevel")
            evo_type = search_pokedex(pokemon_name, "evoType")
            evo_item = search_pokedex(pokemon_name, "evoItem")
            evo_condition = search_pokedex(pokemon_name, "evoCondition")
            
            pokedex = self._load_pokedex()
            
            # Get evolution info
            evolutions = []
            for evo_name in evos:
                # Find evo in pokedex to get its details
                evo_key = evo_name.lower().replace(" ", "").replace(".", "").replace("'", "")
                evo_data = None
                for key, data in pokedex.items():
                    if data.get("name", "").lower() == evo_name.lower() or key == evo_key:
                        evo_data = data
                        break
                
                if evo_data:
                    evo_info = {
                        "name": evo_data.get("name", evo_name),
                        "id": evo_data.get("num", 0),
                        "evoLevel": evo_data.get("evoLevel"),
                        "evoType": evo_data.get("evoType"),
                        "evoItem": evo_data.get("evoItem"),
                        "evoCondition": evo_data.get("evoCondition"),
                        "evoMove": evo_data.get("evoMove"),
                    }
                    evolutions.append(evo_info)
            
            # Get prevo info
            prevo = None
            if prevo_name:
                prevo_key = prevo_name.lower().replace(" ", "").replace(".", "").replace("'", "")
                for key, data in pokedex.items():
                    if data.get("name", "").lower() == prevo_name.lower() or key == prevo_key:
                        prevo = {
                            "name": data.get("name", prevo_name),
                            "id": data.get("num", 0)
                        }
                        break
            
            result = {
                "id": pokemon_id,
                "name": name,
                "types": types,
                "baseStats": base_stats,
                "abilities": abilities,
                "evolutions": evolutions,
                "prevo": prevo,
                "evoLevel": evo_level,
                "evoType": evo_type,
                "evoItem": evo_item,
                "evoCondition": evo_condition,
            }
            
            return json.dumps(result)
        except Exception as e:
            print(f"Error getting Pokemon details: {e}")
            return json.dumps({"error": str(e)})
    
    @pyqtSlot(int, result=str)
    def getPokemonMoves(self, pokemon_id):
        """Get all moves a Pokemon can learn with level info."""
        try:
            # Use existing pokedex_functions to get pokemon name by ID
            pokemon_name = search_pokedex_by_id(pokemon_id)
            print(f"POKEDEX_DEBUG: getPokemonMoves called for ID {pokemon_id}, name: {pokemon_name}")
            
            if not pokemon_name or pokemon_name == "Pokémon not found":
                return json.dumps({"error": "Pokemon not found"})
            
            learnsets = self._load_learnsets()
            moves_data = self._load_moves()
            
            # Normalize name for learnset lookup (like get_all_pokemon_moves does)
            pk_name = pokemon_name.lower()
            pokemon_learnset = learnsets.get(pk_name, {}).get("learnset", {})
            print(f"POKEDEX_DEBUG: Trying pk_name '{pk_name}', found {len(pokemon_learnset)} moves")
            
            # If not found, try variations
            if not pokemon_learnset:
                alt_name = pk_name.replace("-", "").replace(" ", "").replace(".", "").replace("'", "").replace(":", "")
                pokemon_learnset = learnsets.get(alt_name, {}).get("learnset", {})
                print(f"POKEDEX_DEBUG: Trying alt_name '{alt_name}', found {len(pokemon_learnset)} moves")
            
            level_moves = []  # Moves learned by level
            tm_moves = []     # TM/HM moves
            egg_moves = []    # Egg moves
            tutor_moves = []  # Tutor moves
            
            for move_name, learn_methods in pokemon_learnset.items():
                # Get move details using find_details_move (like existing code does)
                move_info = find_details_move(move_name)
                if not move_info:
                    # Fallback to direct lookup
                    move_key = move_name.lower().replace(" ", "")
                    move_info = moves_data.get(move_key, {})
                
                base_move = {
                    "name": move_info.get("name", move_name.title()) if move_info else move_name.title(),
                    "type": move_info.get("type", "Normal") if move_info else "Normal",
                    "category": move_info.get("category", "Physical") if move_info else "Physical",
                    "power": move_info.get("basePower", 0) if move_info else 0,
                    "accuracy": move_info.get("accuracy", 100) if move_info else 100,
                    "pp": move_info.get("pp", 0) if move_info else 0,
                    "description": (move_info.get("shortDesc") or move_info.get("desc", "")) if move_info else "",
                }
                
                # Parse learn methods (format: "9L15" = Gen 9, Level 15, "8M" = Gen 8 TM, etc.)
                for method in learn_methods:
                    if "L" in method:
                        # Level-up move
                        try:
                            parts = method.split("L")
                            level = int(parts[1]) if len(parts) > 1 else 1
                            gen = int(parts[0]) if parts[0] else 9
                            level_move = {**base_move, "level": level, "gen": gen}
                            # Check if we already have this move
                            existing = next((m for m in level_moves if m["name"] == level_move["name"]), None)
                            if existing:
                                # Keep the one from the newer gen or lower level
                                if gen > existing["gen"] or (gen == existing["gen"] and level < existing["level"]):
                                    level_moves.remove(existing)
                                    level_moves.append(level_move)
                            else:
                                level_moves.append(level_move)
                        except (ValueError, IndexError):
                            pass
                    elif "M" in method:
                        # TM/HM move
                        if not any(m["name"] == base_move["name"] for m in tm_moves):
                            tm_moves.append(base_move)
                    elif "E" in method:
                        # Egg move
                        if not any(m["name"] == base_move["name"] for m in egg_moves):
                            egg_moves.append(base_move)
                    elif "T" in method:
                        # Tutor move
                        if not any(m["name"] == base_move["name"] for m in tutor_moves):
                            tutor_moves.append(base_move)
            
            # Sort level moves by level
            level_moves.sort(key=lambda m: m.get("level", 0))
            
            # Sort other moves alphabetically
            tm_moves.sort(key=lambda m: m["name"])
            egg_moves.sort(key=lambda m: m["name"])
            tutor_moves.sort(key=lambda m: m["name"])
            
            result = {
                "levelMoves": level_moves,
                "tmMoves": tm_moves,
                "eggMoves": egg_moves,
                "tutorMoves": tutor_moves,
            }
            
            print(f"POKEDEX_DEBUG: Returning {len(level_moves)} level moves, {len(tm_moves)} TM moves, {len(egg_moves)} egg moves, {len(tutor_moves)} tutor moves")
            return json.dumps(result)
        except Exception as e:
            print(f"Error getting Pokemon moves: {e}")
            import traceback
            traceback.print_exc()
            return json.dumps({"error": str(e)})


class Pokedex(QDialog):
    def __init__(self, addon_dir, ankimon_tracker):
        super().__init__()
        self.addon_dir = addon_dir
        self.ankimon_tracker = ankimon_tracker
        self.owned_pokemon_ids = ankimon_tracker.owned_pokemon_ids
        self.setWindowTitle("Pokedex - Ankimon")

        # Remove default background to make it transparent
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Set a default size for the dialog
        self.resize(900, 800)  # Width: 900px, Height: 800px

        # Create the layout with no margins
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.layout.setSpacing(0)  # Remove spacing between widgets

        # Frame for WebEngineView
        self.frame = QFrame()
        self.frame.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.frame.setFrameStyle(QFrame.Shape.NoFrame)  # Remove frame border

        self.layout.addWidget(self.frame)
        self.setLayout(self.layout)

        # WebEngineView setup
        self.webview = QWebEngineView()
        self.webview.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.frame.setLayout(QVBoxLayout())
        self.frame.layout().setContentsMargins(0, 0, 0, 0)  # Remove margins in frame layout
        self.frame.layout().setSpacing(0)  # Remove spacing
        self.frame.layout().addWidget(self.webview)

        # Set up QWebChannel for JavaScript to Python communication
        self.channel = QWebChannel(self.webview.page())
        self.bridge = PokedexBridge()
        self.channel.registerObject('pokedexBridge', self.bridge)
        self.webview.page().setWebChannel(self.channel)

        # Remove the online/offline buttons since we're focusing on the local Pokédex
        self.load_html()

    def load_html(self):
        self.ankimon_tracker.get_ids_in_collection()
        self.owned_pokemon_ids = self.ankimon_tracker.owned_pokemon_ids
        #print("POKEDEX_DEBUG: Caught Pokémon IDs:", self.owned_pokemon_ids)

        # Convert caught IDs to string
        str_owned_pokemon_ids = ",".join(map(str, self.owned_pokemon_ids)) if self.owned_pokemon_ids else ""
        #print("POKEDEX_DEBUG: Caught IDs string:", str_owned_pokemon_ids)

        # Calculate defeated Pokémon count
        defeated_count = 0
        # Try multiple possible paths for mypokemon.json

        pokemon_list = None

        if os.path.exists(mypokemon_path):
            try:
                with open(mypokemon_path, "r", encoding="utf-8") as file:
                    pokemon_list = json.load(file)
                    print("POKEDEX_DEBUG: Loaded pokemon_list!")

            except json.JSONDecodeError:
                print("POKEDEX_DEBUG: Invalid JSON in mypokemon.json at", mypokemon_path)
            except Exception as e:
                print("POKEDEX_DEBUG: Error reading mypokemon.json at", mypokemon_path, ":", str(e))

        if pokemon_list:
            for pokemon in pokemon_list:
                defeated = pokemon.get("pokemon_defeated", 0)
                try:
                    defeated_num = int(float(str(defeated)))  # Handle int, float, string
                    defeated_count += defeated_num
                    #print(f"POKEDEX_DEBUG: Pokemon ID {pokemon.get('id', 'unknown')}: pokemon_defeated = {defeated_num}")
                except (TypeError, ValueError):
                    print(f"POKEDEX_DEBUG: Invalid pokemon_defeated for ID {pokemon.get('id', 'unknown')}: {defeated}")
        else:
            print("POKEDEX_DEBUG: No valid mypokemon.json found")

        #print("POKEDEX_DEBUG: Total defeated_count =", defeated_count)

        file_path = os.path.join(self.addon_dir, "pokedex", "pokedex.html").replace("\\", "/")
        #print("POKEDEX_DEBUG: Loading HTML from:", file_path)
        url = QUrl.fromLocalFile(file_path)

        query = QUrlQuery()
        query.addQueryItem("numbers", str_owned_pokemon_ids)
        query.addQueryItem("defeated", str(defeated_count))
        url.setQuery(query)
        #print("POKEDEX_DEBUG: Final URL:", url.toString())

        self.webview.setUrl(url)

    def showEvent(self, event):
        self.load_html()
        self.webview.reload()
