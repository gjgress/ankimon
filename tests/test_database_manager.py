import os
import sys
import unittest
from unittest.mock import MagicMock
from pathlib import Path

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

class TestDatabaseManager(unittest.TestCase):
    def setUp(self):
        # Ensure a clean database for each test
        self.db_filename = "test_ankimon.db"
        AnkimonDB.DB_FILENAME = self.db_filename
        self.db = AnkimonDB()

    def tearDown(self):
        self.db.close()
        if os.path.exists(self.db_filename):
            os.remove(self.db_filename)

    def test_get_all_pokemon_caching(self):
        """Test that get_all_pokemon caches results and correctly invalidates."""
        pokemon_1 = {"individual_id": "1", "name": "Pikachu", "level": 5}
        pokemon_2 = {"individual_id": "2", "name": "Charmander", "level": 10}

        # Save a pokemon
        self.db.save_pokemon(pokemon_1)

        # Cache should be None initially
        self.assertIsNone(self.db._all_pokemon_cache)

        # Call get_all_pokemon, which should populate the cache
        all_pokemon = self.db.get_all_pokemon()
        self.assertEqual(len(all_pokemon), 1)
        self.assertEqual(all_pokemon[0]["name"], "Pikachu")

        # Cache should now be populated
        self.assertIsNotNone(self.db._all_pokemon_cache)
        self.assertEqual(len(self.db._all_pokemon_cache), 1)

        # Save a second pokemon, which should invalidate the cache
        self.db.save_pokemon(pokemon_2)
        self.assertIsNone(self.db._all_pokemon_cache)

        # Call get_all_pokemon again
        all_pokemon = self.db.get_all_pokemon()
        self.assertEqual(len(all_pokemon), 2)
        self.assertIsNotNone(self.db._all_pokemon_cache)

    def test_delete_pokemon_invalidates_cache(self):
        """Test that delete_pokemon invalidates the cache."""
        pokemon_1 = {"individual_id": "1", "name": "Pikachu"}
        self.db.save_pokemon(pokemon_1)

        # Populate cache
        self.db.get_all_pokemon()
        self.assertIsNotNone(self.db._all_pokemon_cache)

        # Delete pokemon
        self.db.delete_pokemon("1")
        self.assertIsNone(self.db._all_pokemon_cache)

    def test_save_main_pokemon_invalidates_cache(self):
        """Test that save_main_pokemon invalidates the cache."""
        pokemon_1 = {"individual_id": "1", "name": "Pikachu"}
        self.db.save_pokemon(pokemon_1)

        # Populate cache
        self.db.get_all_pokemon()
        self.assertIsNotNone(self.db._all_pokemon_cache)

        # Save main pokemon
        self.db.save_main_pokemon(pokemon_1)
        self.assertIsNone(self.db._all_pokemon_cache)

    def test_set_main_pokemon_invalidates_cache(self):
        """Test that set_main_pokemon invalidates the cache."""
        pokemon_1 = {"individual_id": "1", "name": "Pikachu"}
        self.db.save_pokemon(pokemon_1)

        # Populate cache
        self.db.get_all_pokemon()
        self.assertIsNotNone(self.db._all_pokemon_cache)

        # Set main pokemon
        self.db.set_main_pokemon("1")
        self.assertIsNone(self.db._all_pokemon_cache)

    def test_has_pokemon_by_name_uses_cache(self):
        """Test that has_pokemon_by_name utilizes the cache."""
        pokemon_1 = {"individual_id": "1", "name": "Pikachu"}
        self.db.save_pokemon(pokemon_1)

        # Populate cache
        self.db.get_all_pokemon()
        self.assertIsNotNone(self.db._all_pokemon_cache)

        # Should return true for Pikachu, using the cache
        self.assertTrue(self.db.has_pokemon_by_name("Pikachu"))
        self.assertTrue(self.db.has_pokemon_by_name("pikachu")) # Case insensitive
        self.assertFalse(self.db.has_pokemon_by_name("Charmander"))

if __name__ == '__main__':
    unittest.main()
