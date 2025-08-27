import sys
import os
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMainWindow, QMenuBar, QMenu
from PyQt6.QtGui import QAction # Corrected import for QAction
from PyQt6.QtCore import Qt
from pathlib import Path

# Add the Ankimon directory to the Python path
# Assuming this script is run from the root of the repository
ANKIMON_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, ANKIMON_ROOT)

# Import necessary Ankimon components
try:
    from src.Ankimon.menu_buttons import create_menu_actions
    from src.Ankimon.pyobj.settings import Settings
    from src.Ankimon.pyobj.InfoLogger import ShowInfoLogger
    from src.Ankimon.pyobj.collection_dialog import PokemonCollectionDialog
    from src.Ankimon.pyobj.item_window import ItemWindow
    from src.Ankimon.pyobj.test_window import TestWindow
    from src.Ankimon.pyobj.achievement_window import AchievementWindow
    from src.Ankimon.pyobj.ankimon_tracker_window import AnkimonTrackerWindow
    from src.Ankimon.pyobj.data_handler_window import DataHandlerWindow
    from src.Ankimon.pyobj.settings_window import SettingsWindow
    from src.Ankimon.pyobj.data_handler import DataHandler
    from src.Ankimon.pyobj.ankimon_shop import PokemonShopManager
    from src.Ankimon.pyobj.trainer_card import TrainerCard
    from src.Ankimon.pyobj.pc_box import PokemonPC
    from src.Ankimon.pokedex.pokedex_obj import Pokedex
    from src.Ankimon.gui_entities import Credits, License, Version_Dialog, TableWidget, IDTableWidget
    from src.Ankimon.gui_classes.pokemon_team_window import PokemonTeamDialog
    from src.Ankimon.gui_classes.check_files import FileCheckerApp
    from src.Ankimon.gui_classes.choose_trainer_sprite import TrainerSpriteDialog
    from src.Ankimon.pyobj.ankimon_leaderboard import show_api_key_dialog
    from src.Ankimon.pyobj.download_sprites import show_agreement_and_download_dialog

    ANKIMON_AVAILABLE = True
except ImportError as e:
    print(f"Could not import Ankimon modules: {e}")
    print("Please ensure Ankimon is installed or its path is correctly set.")
    ANKIMON_AVAILABLE = False

# Import mock classes from the mock_anki package
try:
    from ankimon_test_env.mock_anki import (
        MockReviewerWindow,
        Collection,
        AddonManager,
        ProfileManager,
        MockAnkiApp,
        MockAnkiMainWindow,
        MockAqtUtils,
        qconnect,
        Dialog,
        MainWindow,
        Utils,
        QWebEngineSettings,
        Reviewer,
        DialogManager,
        Menu,
        ReviewerWindow,
        MockTranslator,
        MockSettings,
        MockShowInfoLogger,
        MockTableWidget,
        MockIDTableWidget,
        MockCredits,
        MockLicense,
        MockVersionDialog,
        MockPokemonCollectionDialog,
        MockItemWindow,
        MockTestWindow,
        MockAchievementWindow,
        MockAnkimonTrackerWindow,
        MockDataHandlerWindow,
        MockSettingsWindow,
        MockDataHandler,
        MockPokemonShopManager,
        MockPokedex,
        MockPokemonPC
    )
    MOCKS_AVAILABLE = True
except ImportError as e:
    print(f"Could not import mock classes: {e}")
    MOCKS_AVAILABLE = False


# --- Mock Anki Objects ---
# These mocks are essential for Ankimon's code to run in the test environment.
# They should align with the mocks defined in mock_anki/__init__.py

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

# Global mock 'mw' object for the test environment
# This is the object that Ankimon's code will interact with.
mw = MockAnkiMainWindow()

# --- Test Environment Setup ---

# Mock classes that might be instantiated within menu_buttons.py if not passed as arguments
# These are placeholders to allow menu_buttons.py to be imported and called.
class MockTranslator:
    def __init__(self, language=9):
        self.language = language
        print(f"MockTranslator initialized with language: {language}")

    def translate(self, context, text=None, source=None):
        # Simple translation for demonstration
        if text:
            return f"Translated({text})"
        elif context:
            return f"TranslatedContext({context})"
        return "Translated"

class MockSettings:
    def __init__(self):
        print("MockSettings initialized.")
    def get(self, key, default=None):
        print(f"MockSettings: Getting key '{key}' with default '{default}'")
        return default # Return default for simplicity

class MockShowInfoLogger:
    def __init__(self, name="ShowInfoLogger", log_filename="app.log"):
        print(f"MockShowInfoLogger initialized: {name}, {log_filename}")
        self._log_window_visible = False

    def toggle_log_window(self):
        self._log_window_visible = not self._log_window_visible
        print(f"MockShowInfoLogger: Log window {'shown' if self._log_window_visible else 'hidden'}.")

# Dummy functions for menu actions
def open_team_builder(): print("Mock: Opening team builder...")
def export_to_pkmn_showdown(): print("Mock: Exporting to Showdown...")
def export_all_pkmn_showdown(): print("Mock: Exporting all to Showdown...")
def flex_pokemon_collection(): print("Mock: Flexing collection...")
def open_help_window(online_connectivity): print(f"Mock: Opening help window (online: {online_connectivity})...")
def report_bug(): print("Mock: Reporting bug...")
def rate_addon_url(): print("Mock: Rating addon...")
def join_discord_url(): print("Mock: Joining Discord...")
def open_leaderboard_url(): print("Mock: Opening leaderboard...")
def show_api_key_dialog(): print("Mock: Showing API key dialog...")
def show_agreement_and_download_dialog(): print("Mock: Showing agreement and download dialog...")

# Dummy charts
class MockTableWidget:
    def show_eff_chart(self):
        print("MockTableWidget: show_eff_chart called.")

class MockIDTableWidget:
    def show_gen_chart(self):
        print("MockIDTableWidget: show_gen_chart called.")

# Dummy credits and license
class MockCredits:
    def show_window(self):
        print("MockCredits: show_window called.")

class MockLicense:
    def show_window(self):
        print("MockLicense: show_window called.")

class MockVersionDialog:
    def open(self):
        print("MockVersionDialog: open called.")

# Ankimon key (example)
ankimon_key = "Ctrl+Shift+A"

def run_test_environment():
    """
    Sets up and runs the Ankimon test environment.
    This includes creating mock Anki objects and injecting Ankimon's UI.
    """
    print("Starting Ankimon test environment...")

    # Initialize Ankimon components that need to be passed to create_menu_actions
    # These are mocks or dummy objects for the test environment.
    settings_obj = MockSettings()
    logger = MockShowInfoLogger()
    # Instantiate mock dialogs/windows that menu_buttons.py might expect
    pokecollection_win = MockPokemonCollectionDialog(settings_obj=settings_obj, data_handler_obj=MockDataHandler())
    item_window = MockItemWindow(settings_obj=settings_obj)
    test_window = MockTestWindow(parent=mw.form) # Pass the mock main window as parent
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

    run_test_environment()

    # Start the Qt event loop
    sys.exit(app.exec())
