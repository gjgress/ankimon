# mock_anki/__init__.py
from typing import Union, Optional
from PyQt6.QtWidgets import QWidget, QMainWindow, QMenu, QMenuBar, QVBoxLayout, QApplication, QDialog
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QKeySequence
from .collection import Collection # Import the more detailed Collection class

# Mock classes for dependencies
class Card:
    pass

class MockPokemonCollectionDialog:
    def __init__(self, settings_obj=None, data_handler_obj=None):
        print("MockPokemonCollectionDialog initialized.")
        self.settings_obj = settings_obj
        self.data_handler_obj = data_handler_obj

class Card:
    pass

class MockTestWindow:
    def __init__(self, parent=None):
        print("MockTestWindow initialized.")
        self.parent = parent

class MockAchievementWindow:
    def __init__(self, addon_dir=None, data_handler_obj=None):
        print("MockAchievementWindow initialized.")
        self.addon_dir = addon_dir
        self.data_handler_obj = data_handler_obj
    def show(self):
        print("MockAchievementWindow shown.")

class MockItemWindow:
    def __init__(self, settings_obj=None):
        print("MockItemWindow initialized.")
        self.settings_obj = settings_obj

class MockDataHandler:
    def __init__(self):
        print("MockDataHandler initialized.")

class MockShowInfoLogger:
    def __init__(self):
        print("MockShowInfoLogger initialized.")
    def showInfo(self, message):
        print(f"MockShowInfoLogger: {message}")

class MockSettings:
    def __init__(self):
        print("MockSettings initialized.")
    # Add any methods or attributes that Ankimon's code might call on a settings object
    def get(self, key, default=None):
        print(f"MockSettings: get called for {key}, returning {default}")
        return default
    def set(self, key, value):
        print(f"MockSettings: set called for {key} = {value}")

class AnkiUtils:
    def __init__(self):
        print("MockAnkiUtils initialized.")
    def is_win(self):
        return True # Assume Windows for simplicity in mock
    def isWin(self): # Alias for is_win
        return True

class BuildInfo:
    def __init__(self):
        print("MockAnkiBuildInfo initialized.")
    def version(self):
        return "MockVersion"

class ProfileManager:
    def __init__(self):
        print("MockProfileManager initialized.")
        self.name = "test_profile" # Mock profile name
    def openProfile(self, profile_name):
        print(f"MockProfileManager: Opening profile '{profile_name}'")

class EnemyPokemon:
    pass

class Achievements:
    pass

class Hooks:
    pass

# --- Mock Reviewer and MainWindow for Test Environment ---

class MockReviewerWindow(QMainWindow):
    """
    A mock QMainWindow to simulate Anki's main window,
    allowing for injection of Ankimon UI and menus.
    """
    def __init__(self, parent=None, mw_instance=None):
        super().__init__(parent)
        self.mw = mw_instance
        self.setWindowTitle("Ankimon Test Environment")
        self.setGeometry(100, 100, 800, 600)

        # Setup menubar
        self.menubar = QMenuBar(self)
        self.setMenuBar(self.menubar)

        # Placeholder for injected Ankimon menu
        self.pokemenu = None

        # Central widget to hold injected UI elements
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignCenter) # Center content

        print("MockReviewerWindow initialized.")

    def addMenu(self, menu: QMenu):
        """Adds a QMenu to the menubar."""
        self.menubar.addMenu(menu)
        if menu.title() == "&Ankimon": # Assuming this is how the Ankimon menu is identified
            self.pokemenu = menu

    def inject_widget(self, widget: QWidget):
        """
        Injects a widget into the central area of the reviewer window.
        This simulates how Ankimon UI might be added.
        """
        # Clear existing widgets to make space for the new one
        while self.layout.count():
            item = self.layout.takeAt(0)
            widget_to_remove = item.widget()
            if widget_to_remove:
                widget_to_remove.deleteLater()

        self.layout.addWidget(widget)
        print(f"Widget injected: {widget.objectName() or widget.__class__.__name__}")

    def show(self):
        """Shows the mock reviewer window."""
        super().show()
        print("MockReviewerWindow shown.")

# Mock Anki Main Window (mw) object for the test environment
class MockAnkiMainWindow:
    def __init__(self, addon_dir=None): # Accept addon_dir
        # Use our mock reviewer window as the form, passing mw_instance for full context
        self.form = MockReviewerWindow(mw_instance=self)
        # The reviewer itself is the main window in this mock context
        self.reviewer = self.form
        self.col = Collection(mw_instance=self) # Pass self to collection for scheduler
        self.addonManager = AddonManager(addon_dir=addon_dir) # Pass addon_dir to AddonManager
        self.pm = ProfileManager()
        # Link the app to our reviewer window
        self.app = QApplication.instance() if QApplication.instance() else QApplication([])
        self.app.win = self.form # Ensure app.win points to the form

        # The pokemenu will be set by menu_buttons.py when it's called
        self.pokemenu = None

        print("MockAnkiMainWindow initialized.")

    def show(self):
        self.form.show()



# Mock classes from aqt.qt and aqt.utils if they are directly used by Ankimon code
# For example, if Ankimon directly imports from aqt.qt:
# Mocking aqt.utils functions if they are called directly
class MockAqtUtils:
    def qconnect(self, signal, slot):
        # In a real scenario, this would handle signal connections.
        # For mocks, we can just connect directly if the signal is a PyQt signal.
        try:
            signal.connect(slot)
        except Exception as e:
            print(f"MockAqtUtils.qconnect error: {e}")

    def showWarning(self, msg):
        print(f"MockWarning: {msg}")

    def openLink(self, url):
        print(f"MockOpenLink: Opening URL: {url}")

# Make qconnect available globally for convenience, mimicking aqt.utils
aqt_utils = MockAqtUtils()
qconnect = aqt_utils.qconnect

# Mocking QDialog and QWidget if Ankimon directly instantiates them without a parent
# or expects specific behaviors in the test environment.
# For example, if Ankimon creates dialogs that need to be shown.

# Mocking QApplication and QMainWindow if the test environment needs to manage the event loop
# In run_test_env.py, we'll likely need to create a QApplication instance.

# Mocking QTimer if Ankimon uses it for callbacks
# Mocking QIcon if icons are used and need to be handled.
# Mocking QKeySequence for shortcuts.

# Placeholder for other mock classes if needed by Ankimon's initialization
import json
import os # Added for os.path operations

class AddonManager:
    def __init__(self, addon_dir=None):
        print("MockAddonManager initialized.")
        self.addon_dir = addon_dir if addon_dir is not None else ""
        self._config_cache = {}

    def getConfig(self, addon_id):
        # Assuming Ankimon's config is at 'addon_dir/config.json'
        if addon_id not in self._config_cache:
            config_path = os.path.join(self.addon_dir, "config.json")
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self._config_cache[addon_id] = json.load(f)
                    print(f"MockAddonManager: Loaded config for '{addon_id}' from '{config_path}'")
                except Exception as e:
                    print(f"MockAddonManager: Failed to load config for '{addon_id}' from '{config_path}': {e}")
                    self._config_cache[addon_id] = {} # Fallback to empty config on error
            else:
                print(f"MockAddonManager: Config file not found at '{config_path}' for addon '{addon_id}'.")
                self._config_cache[addon_id] = {} # Fallback to empty config if not found
        return self._config_cache[addon_id]

    def writeConfig(self, addon_id, config):
        # In a mock, we only update the in-memory cache
        print(f"MockAddonManager: Writing config for '{addon_id}': {config}")
        self._config_cache[addon_id] = config

class Dialog:
    def __init__(self, parent=None):
        self.parent = parent
        self.window_title = self.__class__.__name__
        self._is_visible = False
    def setWindowTitle(self, title):
        self.window_title = title
    def show(self):
        self._is_visible = True
        print(f"MockDialog '{self.window_title}' shown.")
    def isVisible(self):
        return self._is_visible
    def exec(self):
        print(f"MockDialog '{self.window_title}' exec called.")
        return QDialog.DialogCode.Accepted # Simulate successful execution

class MainWindow: # This is a mock for Anki's actual MainWindow, not the test env's
    def __init__(self, app=None):
        self.app = app
        self.col = Collection()
        self.addonManager = AddonManager()
        self.reviewer = None # This will be set by the test runner to our MockReviewerWindow
        self.pm = ProfileManager()
        self.form = None # This will be set to our MockReviewerWindow
        self.reviewer_window = None # For enhanced reviewer
        self.pokemenu = None # This will be set by menu_buttons.py
        self.game_menu = None
        print("MockAnkiMainWindow (for Ankimon's internal use) initialized.")

class Utils:
    def __init__(self):
        pass
    def showWarning(self, msg):
        print(f"MockAnkiUtils.showWarning: {msg}")

class QWebEngineSettings:
    pass

class Reviewer: # This is a mock for Anki's actual Reviewer, not the test env's
    def __init__(self):
        print("MockAnkiReviewer initialized.")

class DialogManager:
    def __init__(self):
        print("DialogManager initialized.")
    def open(self, dialog_class, parent=None):
        print(f"DialogManager: Opening dialog {dialog_class.__name__}")
        # In a real scenario, this would instantiate and show the dialog
        # For mock, we can just print or return a mock dialog instance
        instance = dialog_class(parent=parent)
        instance.show() # Simulate showing the dialog
        return instance

class Menu:
    def __init__(self, title):
        self.title = title
        self.actions = []
        print(f"MockMenu '{title}' created.")
    def addMenu(self, title):
        new_menu = Menu(title)
        print(f"MockMenu '{self.title}': Added submenu '{title}'")
        return new_menu
    def addAction(self, action):
        self.actions.append(action)
        print(f"MockMenu '{self.title}': Added action '{action.text()}'")

class ReviewerWindow(Dialog): # Mock for Anki's actual ReviewerWindow
    pass
