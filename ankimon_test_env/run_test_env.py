import sys
import os
import types
import json
from pathlib import Path
from unittest.mock import MagicMock
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QPushButton,
    QMainWindow, QMenuBar, QMenu, QDialog, QGridLayout, QFrame,
    QHBoxLayout, QStatusBar, QSizePolicy
)
from PyQt6.QtGui import QAction, QKeySequence, QPixmap, QFont, QFontDatabase, QGuiApplication, QColor
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
from mock_anki.collection import Collection, MockScheduler

def setup_anki_mocks():
    """Set up comprehensive Anki/AQT mocks in sys.modules"""
    print("Setting up Anki/AQT mocks...")

    from PyQt6.QtWidgets import (
        QApplication, QWidget, QMainWindow, QMenu, QMenuBar, QDialog, QVBoxLayout,
        QHBoxLayout, QLabel, QPushButton, QFrame
    )

    # Create anki module and submodules
    mock_anki = types.ModuleType("anki")
    mock_anki.collection = types.ModuleType("anki.collection")
    mock_anki.cards = types.ModuleType("anki.cards")
    mock_anki.notes = types.ModuleType("anki.notes")
    mock_anki.sched = types.ModuleType("anki.sched")
    mock_anki.utils = types.ModuleType("anki.utils")
    mock_anki.hooks = types.ModuleType("anki.hooks")

    # *** Import only after QApplication created in main()!
    from mock_anki.collection import Collection, MockCard, MockNote, MockScheduler
    mock_anki.collection.Collection = Collection
    mock_anki.cards.Card = MockCard
    mock_anki.notes.Note = MockNote

    # Create aqt module and submodules
    mock_aqt = types.ModuleType("aqt")
    mock_aqt.main = types.ModuleType("aqt.main")
    mock_aqt.reviewer = types.ModuleType("aqt.reviewer")
    mock_aqt.utils = types.ModuleType("aqt.utils")
    mock_aqt.gui_hooks = types.ModuleType("aqt.gui_hooks")
    mock_aqt.qt = types.ModuleType("aqt.qt")
    mock_aqt.webview = types.ModuleType("aqt.webview")
    mock_aqt.operations = types.ModuleType("aqt.operations")
    mock_aqt.operations.scheduling = types.ModuleType("aqt.operations.scheduling")

    # Add reviewer class after QApplication started, see main()
    from mock_aqt.reviewer import MockReviewer
    mock_aqt.reviewer.Reviewer = MockReviewer

    # Mock aqt.utils functions
    def mock_qconnect(signal, slot):
        try:
            signal.connect(slot)
        except Exception as e:
            print(f"MockQConnect error: {e}")

    mock_aqt.utils.qconnect = mock_qconnect
    mock_aqt.utils.showWarning = lambda msg: print(f"MockWarning: {msg}")
    mock_aqt.utils.showInfo = lambda msg: print(f"MockInfo: {msg}")
    mock_aqt.utils.openLink = lambda url: print(f"MockOpenLink: {url}")

    # Mock GUI hooks - create empty lists that add-ons can append to
    mock_hooks = [
        'reviewer_did_show_question', 'reviewer_did_show_answer', 'reviewer_will_answer_card',
        'reviewer_did_answer_card', 'card_will_show', 'reviewer_will_end',
        'reviewer_will_show_context_menu', 'reviewer_will_init_answer_buttons'
    ]

    for hook_name in mock_hooks:
        setattr(mock_aqt.gui_hooks, hook_name, [])

    # Mock Qt classes
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QMainWindow, QMenu, QMenuBar, QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame
    )
    from PyQt6.QtGui import QAction, QKeySequence
    mock_aqt.qt.QApplication = QApplication
    mock_aqt.qt.QMainWindow = QMainWindow
    mock_aqt.qt.QWidget = QWidget
    mock_aqt.qt.QAction = QAction
    mock_aqt.qt.QMenu = QMenu
    mock_aqt.qt.QMenuBar = QMenuBar
    mock_aqt.qt.QDialog = QDialog
    mock_aqt.qt.QVBoxLayout = QVBoxLayout
    mock_aqt.qt.QHBoxLayout = QHBoxLayout
    mock_aqt.qt.QLabel = QLabel
    mock_aqt.qt.QPushButton = QPushButton
    mock_aqt.qt.QFrame = QFrame
    mock_aqt.qt.QKeySequence = QKeySequence

    # Inject into sys.modules
    modules_to_inject = {
        "anki": mock_anki,
        "anki.collection": mock_anki.collection,
        "anki.cards": mock_anki.cards,
        "anki.notes": mock_anki.notes,
        "anki.sched": mock_anki.sched,
        "anki.utils": mock_anki.utils,
        "anki.hooks": mock_anki.hooks,
        "aqt": mock_aqt,
        "aqt.main": mock_aqt.main,
        "aqt.reviewer": mock_aqt.reviewer,
        "aqt.utils": mock_aqt.utils,
        "aqt.gui_hooks": mock_aqt.gui_hooks,
        "aqt.qt": mock_aqt.qt,
        "aqt.webview": mock_aqt.webview,
        "aqt.operations": mock_aqt.operations,
        "aqt.operations.scheduling": mock_aqt.operations.scheduling,
    }

    for module_name, module_obj in modules_to_inject.items():
        sys.modules[module_name] = module_obj

    print("Anki/AQT mocks injected into sys.modules")


def create_mock_objects_for_ankimon():
    """Create mock objects that Ankimon's menu system expects"""

    class MockObject:
        def __init__(self, name="MockObject"):
            self.name = name
        def __call__(self, *args, **kwargs):
            print(f"{self.name} called with args: {args}, kwargs: {kwargs}")
            return self
        def __getattr__(self, name):
            return MockObject(f"{self.name}.{name}")
        def show(self):
            print(f"{self.name}.show() called")
        def exec(self):
            print(f"{self.name}.exec() called")
            return True
        def show_window(self):
            print(f"{self.name}.show_window() called")
        def open_dynamic_window(self):
            print(f"{self.name}.open_dynamic_window() called - Starting reviewer")
            if hasattr(sys.modules.get('aqt'), 'mw') and sys.modules['aqt'].mw:
                sys.modules['aqt'].mw.reviewer.show()
        def toggle_window(self):
            print(f"{self.name}.toggle_window() called")

    mock_objects = {
        'database_complete': True,
        'online_connectivity': False,
        'pokecollection_win': None,
        'item_window': MockObject("ItemWindow"),
        'test_window': MockObject("TestWindow"),
        'achievement_bag': MockObject("AchievementWindow"),
        'open_team_builder': MockObject("open_team_builder"),
        'export_to_pkmn_showdown': MockObject("export_to_pkmn_showdown"),
        'export_all_pkmn_showdown': MockObject("export_all_pkmn_showdown"),
        'flex_pokemon_collection': MockObject("flex_pokemon_collection"),
        'eff_chart': MockObject("EffChart"),
        'gen_id_chart': MockObject("GenIDChart"),
        'credits': MockObject("Credits"),
        'license': MockObject("License"),
        'open_help_window': MockObject("open_help_window"),
        'report_bug': MockObject("report_bug"),
        'rate_addon_url': MockObject("rate_addon_url"),
        'version_dialog': MockObject("VersionDialog"),
        'trainer_card': MockObject("TrainerCard"),
        'ankimon_tracker_window': MockObject("AnkimonTrackerWindow"),
        'logger': MockObject("Logger"),
        'data_handler_window': MockObject("DataHandlerWindow"),
        'settings_window': MockObject("SettingsWindow"),
        'shop_manager': MockObject("ShopManager"),
        'pokedex_window': MockObject("PokedexWindow"),
        'ankimon_key': 'Ctrl+K',
        'join_discord_url': MockObject("join_discord_url"),
        'open_leaderboard_url': MockObject("open_leaderboard_url"),
        'settings_obj': MockObject("Settings"),
        'addon_dir': Path(__file__).parent.parent / "src" / "Ankimon",
        'data_handler_obj': MockObject("DataHandler"),
        'pokemon_pc': MockObject("PokemonPC"),
    }
    return mock_objects

def setup_global_mw(main_window, reviewer):
    """Set up the global mw object that Ankimon expects"""
    mw = type('MockMainWindow', (), {})()
    mw.form = main_window
    mw.col = Collection()
    mw.col.sched = MockScheduler(mw)
    mw.reviewer = reviewer
    mw.addonManager = type('MockAddonManager', (), {
        'getConfig': lambda self, addon_id: {},
        'writeConfig': lambda self, addon_id, config: print(f"Writing config for {addon_id}: {config}")
    })()
    mw.pm = type('MockProfileManager', (), {
        'openProfile': lambda self, name: print(f"Opening profile: {name}")
    })()
    from PyQt6.QtWidgets import QApplication, QMenu
    mw.app = QApplication.instance()
    try:
        settings_mock = type('MockSettings', (), {
            'get': lambda self, key, default=None: 9 if key == "misc.language" else default
        })()
        mw.translator = type('MockTranslator', (), {
            'translate': lambda self, key: key.replace("_", " ").title()
        })()
        mw.pokemenu = QMenu('Ankimon', main_window)
        print("Mock mw object configured with translator and pokemenu")
    except Exception as e:
        print(f"Error setting up translator/menu: {e}")
    return mw

def load_ankimon_addon(mw):
    """Load and initialize Ankimon addon"""
    print("\n--- Loading Ankimon Add-on ---")
    try:
        ankimon_path = Path(__file__).parent.parent / "src" / "Ankimon"
        if str(ankimon_path) not in sys.path:
            sys.path.insert(0, str(ankimon_path))
            print(f"Added Ankimon path to sys.path: {ankimon_path}")
        sys.modules['aqt'].mw = mw
        sys.modules['aqt.main'].mw = mw
        try:
            from menu_buttons import create_menu_actions
            print("Successfully imported menu_buttons")
            mock_objects = create_mock_objects_for_ankimon()
            create_menu_actions(**mock_objects)
            if mw.pokemenu:
                mw.form.menubar.addMenu(mw.pokemenu)
                print("Ankimon menu added to menubar")
        except ImportError as e:
            print(f"Could not import menu_buttons: {e}")
            print("Adding fallback menu...")
        test_menu = mw.form.menubar.addMenu("Review")
        start_action = test_menu.addAction("Start Review")
        start_action.triggered.connect(mw.reviewer.show)
        print("Ankimon integration completed")
    except Exception as e:
        print(f"Error during Ankimon integration: {e}")
        import traceback
        traceback.print_exc()
        test_menu = mw.form.menubar.addMenu("Test")
        start_action = test_menu.addAction("Start Review (Fallback)")
        start_action.triggered.connect(mw.reviewer.show)
        print("Fallback menu added")

class TestEnvironmentMainWindow(QMainWindow):
    """Main window for the Ankimon test environment"""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Ankimon Test Environment - Reviewer")
        self.setGeometry(100, 100, 1200, 800)
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        self.reviewer_container = QWidget()
        self.reviewer_layout = QVBoxLayout(self.reviewer_container)
        layout.addWidget(self.reviewer_container)
        self.menubar = QMenuBar(self)
        self.setMenuBar(self.menubar)
        print("TestEnvironmentMainWindow initialized")
    def setup_reviewer(self, reviewer):
        self.reviewer_layout.addWidget(reviewer.web.qwebengine_view)
        reviewer.bottom.web.qwebengine_view.setMaximumHeight(100)
        self.reviewer_layout.addWidget(reviewer.bottom.web.qwebengine_view)
        print("Reviewer setup in main window")

def main():
    print("=== Ankimon Test Environment Starting ===")

    # [1] Import PyQt6 widgets and create QApplication FIRST.
    app = QApplication(sys.argv)

    # [2] Now that Qt classes are available, do *all* subclassing *here*:

    class TestEnvironmentMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Ankimon Test Environment - Reviewer")
            self.setGeometry(100, 100, 1200, 800)
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            layout = QVBoxLayout(central_widget)
            self.reviewer_container = QWidget()
            self.reviewer_layout = QVBoxLayout(self.reviewer_container)
            layout.addWidget(self.reviewer_container)
            self.menubar = QMenuBar(self)
            self.setMenuBar(self.menubar)
            print("TestEnvironmentMainWindow initialized")
        def setup_reviewer(self, reviewer):
            self.reviewer_layout.addWidget(reviewer.web.qwebengine_view)
            reviewer.bottom.web.qwebengine_view.setMaximumHeight(100)
            self.reviewer_layout.addWidget(reviewer.bottom.web.qwebengine_view)
            print("Reviewer setup in main window")

    # Now import your mocks (which may reference PyQt classes)
    setup_anki_mocks()
    from mock_aqt.reviewer import MockReviewer
    from mock_anki.collection import MockScheduler, Collection

    main_window = TestEnvironmentMainWindow()
    ankimon_root = Path(__file__).parent.parent
    reviewer = MockReviewer(None)
    reviewer.web.ankimon_root = ankimon_root
    reviewer.bottom.web.ankimon_root = ankimon_root
    main_window.setup_reviewer(reviewer)
    mw = setup_global_mw(main_window, reviewer)
    reviewer.mw = mw
    load_ankimon_addon(mw)
    main_window.show()

    print("\n=== Ankimon Test Environment Ready ===")
    print("Use 'Review > Start Review' or 'Ankimon' menu to begin card review")
    print("Expected workflow: Question -> Show Answer -> Ease buttons -> Next card")
    print("The Ankimon HUD should appear as an overlay on the card content")

    sys.exit(app.exec())

if __name__ == "__main__":
    main()