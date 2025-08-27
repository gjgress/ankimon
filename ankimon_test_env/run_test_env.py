import sys
import os
# Ensure QAction is imported ONLY from PyQt6.QtGui at the very top.
from PyQt6.QtGui import QAction
# Explicitly import only the necessary components from QtWidgets, excluding QAction.
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMainWindow, QMenuBar, QMenu, QDialog
from PyQt6.QtCore import Qt
from pathlib import Path

print("---- Python version:", sys.version)

try:
    import PyQt6
    print("PyQt6 path:", PyQt6.__file__)
    # This check confirms QAction is available in QtGui.
    print("QAction exists?:", 'QAction' in dir(PyQt6.QtGui))
except Exception as e:
    print("PyQt6 import or QAction error:", e)

# --- Debugging: Check for QAction import from QtWidgets ---
print("\n--- Debugging QAction import ---")
try:
    # This import should FAIL if QAction is still being imported from QtWidgets
    # and cause the ImportError we're seeing.
    # We are explicitly trying to import QAction from QtWidgets here to trigger the error
    # if it's still present in that module's namespace in a way that causes conflict.
    from PyQt6.QtWidgets import QAction as QtWidgets_QAction
    print("Successfully imported QAction from PyQt6.QtWidgets (this should not happen if the error is real).")
except ImportError as e:
    print(f"Caught expected ImportError for QAction from QtWidgets: {e}")
print("---\n--- End Debugging QAction import ---\n")


# Add the Ankimon directory to the Python path
# Assuming this script is run from the root of the repository
ANKIMON_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ANKIMON_ROOT)

# Import mock classes from the mock_anki package FIRST
# This ensures that classes like MockReviewerWindow are defined before they are used
# in the definition of MockAnkiMainWindow.
print("Attempting to import mock classes...")
try:
    from ankimon_test_env.mock_anki import (
        MockReviewerWindow,
        Collection,
        AddonManager,
        ProfileManager,
        MockSettings,
        MockShowInfoLogger,
        MockPokemonCollectionDialog,
        MockDataHandler,
        MockItemWindow,
        MockTestWindow,
        MockAchievementWindow
    )
    MOCKS_AVAILABLE = True
    print("Successfully imported MockReviewerWindow, Collection, AddonManager, ProfileManager, and MockSettings.")
except ImportError as e:
    print(f"Failed to import MockReviewerWindow, Collection, AddonManager, ProfileManager, or MockSettings: {e}")
    MOCKS_AVAILABLE = False


# Mock Anki App
class MockAnkiApp:
    def __init__(self):
        # 'win' attribute usually points to the main Anki window
        self.win = None
        print("MockAnkiApp initialized.")

# Mock Anki MainWindow (mw)
class MockAnkiMainWindow:
    def __init__(self):
        # This mock represents the Anki main window object that Ankimon interacts with.
        # It needs to have a menubar and a way to add menus.
        # Note: self.form is created here, but MockReviewerWindow (which it uses) is a QMainWindow.
        # This MockAnkiMainWindow init method will now be called *after* QApplication is set up.
        self.form = MockReviewerWindow() # Our simulated reviewer window
        self.menubar = self.form.menubar # Access the menubar from the reviewer window
        self.pokemenu = None # This will be populated by create_menu_actions

        # Mock other attributes Ankimon might access on mw
        self.col = Collection() # From mock_anki/__init__.py
        self.addonManager = AddonManager() # From mock_anki/__init__.py
        self.reviewer = self.form # Link to our mock reviewer window
        self.pm = ProfileManager() # From mock_anki/__init__.py
        self.app = MockAnkiApp()
        self.app.win = self.form # Link the app to our reviewer window

        print("MockAnkiMainWindow initialized.")

    def show(self):
        self.form.show()


# Global placeholders for mw and Ankimon imports, to be set after QApplication is initialized
mw = None
create_menu_actions = None
ankimon_key = None
join_discord_url = None
open_leaderboard_url = None
rate_addon_url = None
open_team_builder = None
export_to_pkmn_showdown = None
export_all_pkmn_showdown = None
flex_pokemon_collection = None
open_help_window = None
report_bug = None
ANKIMON_AVAILABLE = False


# Define dummy classes for Ankimon UI elements that are instantiated in the test environment
# These are minimal implementations to satisfy instantiation and basic method calls.
class MockAnkimonTrackerWindow(QDialog):
    def __init__(self, settings_obj=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_obj = settings_obj
    def show(self): pass
    def setWindowTitle(self, title): pass

class MockDataHandlerWindow(QDialog):
    def __init__(self, settings_obj=None, data_handler_obj=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_obj = settings_obj
        self.data_handler_obj = data_handler_obj
    def show(self): pass
    def setWindowTitle(self, title): pass

class MockSettingsWindow(QDialog):
    def __init__(self, settings_obj=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_obj = settings_obj
    def show(self): pass
    def setWindowTitle(self, title): pass

class MockPokemonShopManager(QDialog):
    def __init__(self, settings_obj=None, data_handler_obj=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_obj = settings_obj
        self.data_handler_obj = data_handler_obj
    def show(self): pass
    def setWindowTitle(self, title): pass

class MockPokedex(QDialog):
    def __init__(self, settings_obj=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_obj = settings_obj
    def show(self): pass
    def setWindowTitle(self, title): pass

class MockPokemonPC(QDialog):
    def __init__(self, settings_obj=None, data_handler_obj=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.settings_obj = settings_obj
        self.data_handler_obj = data_handler_obj
    def show(self): pass
    def setWindowTitle(self, title): pass

class MockTableWidget(QWidget):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs)
    def show(self): pass

class MockIDTableWidget(QWidget):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs)
    def show(self): pass

class MockCredits(QDialog):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs)
    def show(self): pass
    def setWindowTitle(self, title): pass

class MockLicense(QDialog):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs)
    def show(self): pass
    def setWindowTitle(self, title): pass

class MockVersionDialog(QDialog):
    def __init__(self, *args, **kwargs): super().__init__(*args, **kwargs)
    def show(self): pass
    def setWindowTitle(self, title): pass

def run_test_environment():
    """
    Sets up and runs the Ankimon test environment.
    This includes creating mock Anki objects and injecting Ankimon's UI.
    """
    # Declare global variables that will be populated in this function
    global mw, create_menu_actions, ankimon_key, join_discord_url, open_leaderboard_url, rate_addon_url, ANKIMON_AVAILABLE, \
           open_team_builder, export_to_pkmn_showdown, export_all_pkmn_showdown, flex_pokemon_collection, open_help_window, report_bug

    print("Starting Ankimon test environment...")

    # Create the global mock 'mw' object AFTER QApplication is guaranteed to exist.
    mw = MockAnkiMainWindow()

    # Mock `aqt` and the global `mw` object so Ankimon modules can be imported.
    from types import ModuleType
    try:
        import aqt
        aqt.mw = mw
    except ImportError:
        # If aqt is not installed (e.g., in a clean CI environment),
        # create a mock module and inject it into sys.modules so the import doesn't fail.
        aqt_mock = ModuleType('aqt')
        aqt_mock.mw = mw
        sys.modules['aqt'] = aqt_mock

    # Import actual Ankimon functions and constants AFTER mw is set up
    try:
        from src.Ankimon.menu_buttons import create_menu_actions
        from src.Ankimon.consts import ANKIMON_KEY as ankimon_key, JOIN_DISCORD_URL as join_discord_url, OPEN_LEADERBOARD_URL as open_leaderboard_url, RATE_ADDON_URL as rate_addon_url
        from src.Ankimon.functions.utils import open_team_builder, export_to_pkmn_showdown, export_all_pkmn_showdown, flex_pokemon_collection, open_help_window, report_bug
        
        ANKIMON_AVAILABLE = True
        print("Successfully imported Ankimon core modules.")
    except ImportError as e:
        print(f"Failed to import Ankimon core modules (src.Ankimon.*): {e}")
        # Define dummy functions and variables if Ankimon modules are not available
        # to prevent NameErrors later in the script if MOCKS_AVAILABLE is True.
        def create_menu_actions(*args, **kwargs): pass
        def open_team_builder(*args, **kwargs): pass
        def export_to_pkmn_showdown(*args, **kwargs): pass
        def export_all_pkmn_showdown(*args, **kwargs): pass
        def flex_pokemon_collection(*args, **kwargs): pass
        def open_help_window(*args, **kwargs): pass
        def report_bug(*args, **kwargs): pass
        rate_addon_url = "http://mock.rate.addon.url"
        ankimon_key = "mock_ankimon_key"
        join_discord_url = "http://mock.discord.url"
        open_leaderboard_url = "http://mock.leaderboard.url"
        ANKIMON_AVAILABLE = False # Redundant, but explicit

    # Initialize Ankimon components that need to be passed to create_menu_actions
    # These are mocks or dummy objects for the test environment.
    settings_obj = MockSettings()
    logger = MockShowInfoLogger()
    # Instantiate mock dialogs/windows that menu_buttons.py might expect
    pokecollection_win = MockPokemonCollectionDialog(settings_obj=settings_obj, data_handler_obj=MockDataHandler())
    item_window = MockItemWindow(settings_obj=settings_obj)
    # The parent for MockTestWindow needs to be mw.form, which is now available.
    test_window = MockTestWindow(parent=mw.form)
    achievement_bag = MockAchievementWindow(addon_dir=Path(ANKIMON_ROOT), data_handler_obj=MockDataHandler())
    ankimon_tracker_window = MockAnkimonTrackerWindow(settings_obj=settings_obj)
    data_handler_window = MockDataHandlerWindow(settings_obj=settings_obj, data_handler_obj=MockDataHandler())
    settings_window = MockSettingsWindow(settings_obj=settings_obj)
    data_handler_obj = MockDataHandler()
    shop_manager = MockPokemonShopManager(settings_obj=settings_obj, data_handler_obj=data_handler_obj)
    pokedex_window = MockPokedex(settings_obj=settings_obj)
    trainer_card = object() # Mock object
    pokemon_pc = MockPokemonPC(settings_obj=settings_obj, data_handler_obj=data_handler_obj)

    # Create the Ankimon menu and actions
    # This function will add the 'Ankimon' menu to mw.menubar (which is mw.form.menubar)
    if ANKIMON_AVAILABLE:
        create_menu_actions(
            database_complete=True, 
            online_connectivity=True, # Assume online for testing
            pokecollection_win=pokecollection_win,
            item_window=item_window,
            test_window=test_window,
            achievement_bag=achievement_bag,
            open_team_builder=open_team_builder,
            export_to_pkmn_showdown=export_to_pkmn_showdown,
            export_all_pkmn_showdown=export_all_pkmn_showdown,
            flex_pokemon_collection=flex_pokemon_collection,
            eff_chart=MockTableWidget(),
            gen_id_chart=MockIDTableWidget(),
            credits=MockCredits(),
            license=MockLicense(),
            open_help_window=open_help_window,
            report_bug=report_bug,
            rate_addon_url=rate_addon_url,
            version_dialog=MockVersionDialog(),
            trainer_card=trainer_card,
            ankimon_tracker_window=ankimon_tracker_window,
            logger=logger,
            data_handler_window=data_handler_window,
            settings_window=settings_window,
            shop_manager=shop_manager,
            pokedex_window=pokedex_window,
            ankimon_key=ankimon_key,
            join_discord_url=join_discord_url,
            open_leaderboard_url=open_leaderboard_url,
            settings_obj=settings_obj,
            addon_dir=Path(ANKIMON_ROOT),
            data_handler_obj=data_handler_obj,
            pokemon_pc=pokemon_pc,
        )

        # --- Inject Ankimon UI into the reviewer window ---
        # Placeholder for the main Ankimon UI widget
        ankimon_ui_widget = QWidget()
        ankimon_ui_widget.setObjectName("AnkimonMainUI")
        ankimon_ui_layout = QVBoxLayout(ankimon_ui_widget)
        ankimon_ui_layout.addWidget(QLabel("Ankimon UI Placeholder"))
        ankimon_ui_layout.addWidget(QPushButton("Ankimon Action Button"))

        # Inject this widget into our mock reviewer window
        if hasattr(mw.form, 'inject_widget'):
            mw.form.inject_widget(ankimon_ui_widget)
        else:
            print("Error: MockReviewerWindow does not have 'inject_widget' method.")

    else:
        print("Ankimon modules not available. Skipping UI injection and menu creation.")
        # Show a basic window if Ankimon is not available
        mw.form.layout.addWidget(QLabel("Ankimon not available. Test environment running with basic UI."))

    # Show the main mock window (which contains the injected UI)
    mw.show()

    print("Test environment setup complete. Showing mock window.")

if __name__ == '__main__':
    # Ensure a QApplication instance exists
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    # The rest of the setup and execution happens within run_test_environment()
    # which is called after all necessary imports are done.
    run_test_environment()

    # Start the Qt event loop
    sys.exit(app.exec())
