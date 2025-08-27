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

    # --- Robustly Mock Anki Core Modules ---
    # This section ensures that all Anki-related imports in Ankimon code
    # are directed to our mock objects, preventing "partially initialized module" errors.
    from types import ModuleType

    # Helper to ensure a mock module exists and is put into sys.modules
    def ensure_mock_module(name: str):
        if name in sys.modules:
            # If already imported (e.g., real Anki module), remove it
            # This is critical to prevent "partially initialized module" errors.
            print(f"Warning: Real '{name}' module found in sys.modules. Overriding with mock.")
            del sys.modules[name]
        mock_module = ModuleType(name)
        sys.modules[name] = mock_module
        return mock_module

    # Mock 'anki' and its submodules
    anki_mock_module = ensure_mock_module('anki')
    
    # Mock anki.models
    anki_models_mock = ensure_mock_module('anki.models')
    class NotetypeDict(dict): # Define a simple mock for NotetypeDict
        pass
    anki_models_mock.NotetypeDict = NotetypeDict
    anki_mock_module.models = anki_models_mock

    # Mock anki.collection
    anki_collection_mock = ensure_mock_module('anki.collection')
    anki_collection_mock.Collection = Collection # Use our already defined MockCollection class
    anki_mock_module.collection = anki_collection_mock

    # Mock anki.hooks (Ankimon often uses Anki's hook system)
    anki_hooks_mock = ensure_mock_module('anki.hooks')

    # Define mock functions for common hook operations
    import functools

    def wrap(old_func, new_func, pos="after"):
        """
        Mock implementation of anki.hooks.wrap for test environment.
        In Anki, this is used to wrap/decorate existing functions.
        For testing, we'll create a basic wrapper that preserves functionality.
        """
        if pos == "before":
            @functools.wraps(old_func)
            def wrapper(*args, **kwargs):
                new_func(*args, **kwargs)
                return old_func(*args, **kwargs)
        elif pos == "after":
            @functools.wraps(old_func)
            def wrapper(*args, **kwargs):
                result = old_func(*args, **kwargs)
                new_func(*args, **kwargs)
                return result
        elif pos == "around":
            @functools.wraps(old_func)
            def wrapper(*args, **kwargs):
                return new_func(old_func, *args, **kwargs)
        else:
            # Default to "after" behavior
            @functools.wraps(old_func)
            def wrapper(*args, **kwargs):
                result = old_func(*args, **kwargs)
                new_func(*args, **kwargs)
                return result
        return wrapper

    def runHook(hook_name, *args):
        """Mock runHook - just pass through silently for testing"""
        pass

    def runFilter(hook_name, value, *args):
        """Mock runFilter - return the value unchanged for testing"""
        return value

    def addHook(hook_name, func):
        """Mock addHook - already implemented but ensure it exists"""
        pass

    def remHook(hook_name, func):
        """Mock remHook - already implemented but ensure it exists"""  
        pass

    anki_hooks_mock.addHook = addHook
    anki_hooks_mock.remHook = remHook
    anki_hooks_mock.runHook = runHook
    anki_hooks_mock.runFilter = runFilter
    anki_hooks_mock.wrap = wrap # Assign the detailed mock wrap function

    anki_mock_module.hooks = anki_hooks_mock # Link to the main anki mock


    # --- Robustly Mock aqt Modules ---
    # This ensures 'aqt' and its necessary submodules are mocked.
    aqt_mock_module = ensure_mock_module('aqt')

    # Unconditionally set mw attribute on aqt
    aqt_mock_module.mw = mw

    # Mock aqt.gui_hooks
    aqt_gui_hooks_mock = ensure_mock_module('aqt.gui_hooks')
    class MockGuiHooks:
        def reviewer_will_show_question(self, *args): pass
        def reviewer_did_show_answer(self, *args): pass
        def editor_did_init_note(self, *args): pass
        def editor_did_load_note(self, *args): pass
        def deck_browser_did_render(self, *args): pass
        def profile_did_open(self, *args): pass
        def profile_will_close(self, *args): pass
        def collection_did_flush(self, *args): pass
        def add_cards_did_add_note(self, *args): pass
        def add_cards_will_add_note(self, *args): pass
        def add_cards_did_add_cards(self, *args): pass
        def browser_did_reset(self, *args): pass
        def webview_will_set_content(self, *args): pass
        # Add other gui_hooks as needed if more ImportError issues arise
    
    aqt_gui_hooks_mock.__dict__.update(MockGuiHooks().__dict__) # Assign methods to the mock module
    aqt_mock_module.gui_hooks = aqt_gui_hooks_mock


    # Mock aqt.qt - crucial for `from aqt.qt import *` in menu_buttons.py
    aqt_qt_mock = ensure_mock_module('aqt.qt')
    # Re-export the necessary PyQt6 classes that `menu_buttons.py` might expect.
    # These are already imported by run_test_env.py at the top, so we can access them.
    aqt_qt_mock.QAction = QAction
    aqt_qt_mock.QApplication = QApplication
    aqt_qt_mock.QWidget = QWidget
    aqt_qt_mock.QVBoxLayout = QVBoxLayout
    aqt_qt_mock.QLabel = QLabel
    aqt_qt_mock.QPushButton = QPushButton
    aqt_qt_mock.QMainWindow = QMainWindow
    aqt_qt_mock.QMenuBar = QMenuBar
    aqt_qt_mock.QMenu = QMenu
    aqt_qt_mock.QDialog = QDialog
    aqt_qt_mock.Qt = Qt
    aqt_mock_module.qt = aqt_qt_mock

    # Mock aqt.utils
    aqt_utils_mock = ensure_mock_module('aqt.utils')
    # Use the MockAqtUtils class defined in mock_anki
    from ankimon_test_env.mock_anki import MockAqtUtils
    aqt_utils_mock.__dict__.update(MockAqtUtils().__dict__)
    aqt_mock_module.utils = aqt_utils_mock

    # Mock aqt.reviewer
    aqt_reviewer_mock = ensure_mock_module('aqt.reviewer')
    # If specific attributes of aqt.reviewer are needed later, they can be added here.
    # For now, just ensuring the module exists should resolve the import error.
    aqt_mock_module.reviewer = aqt_reviewer_mock

    # Import actual Ankimon functions and constants AFTER mw and all anki/aqt mocks are set up
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
