import sys
import os
from unittest.mock import MagicMock
from pathlib import Path
import time

sys.path.insert(0, os.path.abspath('src'))
import importlib.util

# Load the module manually without loading Ankimon.__init__
spec = importlib.util.spec_from_file_location("Ankimon.resources", "src/Ankimon/resources.py")
resources = importlib.util.module_from_spec(spec)
sys.modules["Ankimon"] = MagicMock()
sys.modules["Ankimon.resources"] = resources
resources.user_path = Path('.')

spec_db = importlib.util.spec_from_file_location("Ankimon.pyobj.database_manager", "src/Ankimon/pyobj/database_manager.py")
dbm = importlib.util.module_from_spec(spec_db)
sys.modules["Ankimon.pyobj"] = MagicMock()
sys.modules["Ankimon.pyobj.database_manager"] = dbm
spec_db.loader.exec_module(dbm)

AnkimonDB = dbm.AnkimonDB
db = AnkimonDB()

# Create dummy data to test performance
print("Inserting dummy pokemon...")
start_time = time.time()
for i in range(1000):
    db.save_pokemon({
        "individual_id": f"dummy_{i}",
        "name": f"Pokemon_{i}",
        "id": i,
        "level": 50,
        "stats": {"hp": 100, "atk": 100, "def": 100, "spa": 100, "spd": 100, "spe": 100}
    })
print(f"Insert time: {time.time() - start_time:.4f}s")

print("Testing get_all_pokemon()...")
start_time = time.time()
all_pokemon = db.get_all_pokemon()
elapsed = time.time() - start_time
print(f"Fetched {len(all_pokemon)} pokemon in {elapsed:.4f}s")

print("Testing get_all_pokemon() again (cached? no)...")
start_time = time.time()
all_pokemon = db.get_all_pokemon()
elapsed = time.time() - start_time
print(f"Fetched {len(all_pokemon)} pokemon in {elapsed:.4f}s")

print("Testing get_all_pokemon_ids()...")
start_time = time.time()
ids = db.get_all_pokemon_ids()
elapsed = time.time() - start_time
print(f"Fetched {len(ids)} pokemon IDs in {elapsed:.4f}s")

print("Testing has_pokemon_by_name()...")
start_time = time.time()
db.has_pokemon_by_name("Pokemon_999")
elapsed = time.time() - start_time
print(f"Checked has_pokemon_by_name in {elapsed:.4f}s")

# Clean up
db.close()
if os.path.exists("ankimon.db"):
    os.remove("ankimon.db")
