import webbrowser
import sys
import os
import types
import json
import shutil
from pathlib import Path
from unittest.mock import MagicMock

# Add project root and src to sys.path to allow for absolute imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Define the Ankimon addon directory for easy access
ANKIMON_ADDON_DIR = Path(__file__).parent.parent / "src" / "Ankimon"

def setup_anki_mocks():
    """Set up comprehensive Anki/AQT mocks in sys.modules"""
    print("Setting up Anki/AQT mocks...")

    # Create anki module and submodules
    mock_anki = types.ModuleType("anki")
    mock_anki.collection = types.ModuleType("anki.collection")
    mock_anki.cards = types.ModuleType("anki.cards")
    mock_anki.notes = types.ModuleType("anki.notes")
    mock_anki.sched = types.ModuleType("anki.sched")
    mock_anki.utils = types.ModuleType("anki.utils")
    mock_anki.utils.isWin = lambda: True
    mock_anki.utils.is_win = lambda: True
    mock_anki.hooks = types.ModuleType("anki.hooks")
    mock_anki.hooks.addHook = lambda name, func: None
    mock_anki.buildinfo = types.ModuleType("anki.buildinfo")
    mock_anki.buildinfo.version = "2.1.54"

    # Create aqt module and submodules
    mock_aqt = types.ModuleType("aqt")
    mock_aqt.main = types.ModuleType("aqt.main")
    mock_aqt.reviewer = types.ModuleType("aqt.reviewer")
    mock_aqt.utils = types.ModuleType("aqt.utils")
    mock_aqt.gui_hooks = types.ModuleType("aqt.gui_hooks")
    mock_aqt.qt = types.ModuleType("aqt.qt")
    mock_aqt.webview = types.ModuleType("aqt.webview")
    mock_aqt.sound = types.ModuleType("aqt.sound")
    mock_aqt.toolbar = types.ModuleType("aqt.toolbar")
    mock_aqt.theme = types.ModuleType("aqt.theme")
    mock_aqt.operations = types.ModuleType("aqt.operations")
    mock_aqt.operations.scheduling = types.ModuleType("aqt.operations.scheduling")

    from PyQt6.QtWidgets import QDialog, QVBoxLayout
    from PyQt6.QtWebEngineWidgets import QWebEngineView

    # Mock aqt.utils functions
    def mock_qconnect(signal, slot):
        try:
            signal.connect(slot)
        except Exception as e:
            print(f"MockQConnect error: {e}")

    mock_aqt.utils.qconnect = mock_qconnect
    mock_aqt.qconnect = mock_qconnect
    mock_aqt.QDialog = QDialog
    mock_aqt.QVBoxLayout = QVBoxLayout
    mock_aqt.QWebEngineView = QWebEngineView
    mock_aqt.utils.showWarning = lambda msg, parent=None, title="Warning": print(f"MockWarning: {msg}")
    mock_aqt.utils.showInfo = lambda msg, parent=None, title="Info": print(f"MockInfo: {msg}")
    mock_aqt.utils.tooltip = lambda msg, period=3000: print(f"MockTooltip: {msg}")
    mock_aqt.utils.openLink = lambda url: webbrowser.open_new_tab(url)

    # Mock GUI hooks
    class MockHook:
        def __init__(self, name=""):
            self.name = name
            self.hooks = []
        def append(self, func):
            print(f"Appending to hook: {self.name}")
            self.hooks.append(func)
        def remove(self, func):
            if func in self.hooks:
                self.hooks.remove(func)
        def __call__(self, *args, **kwargs):
            for hook in self.hooks:
                try:
                    hook(*args, **kwargs)
                except:
                    pass # Anki ignores hook errors

        def run(self, *args, **kwargs):
            self(*args, **kwargs)

    mock_aqt.gui_hooks.addon_config_editor_will_display_json = MockHook("addon_config_editor_will_display_json")
    mock_aqt.gui_hooks.addon_config_editor_will_save_json = MockHook("addon_config_editor_will_save_json")
    mock_aqt.gui_hooks.sync_did_finish = MockHook("sync_did_finish")
    mock_aqt.gui_hooks.reviewer_did_show_question = MockHook("reviewer_did_show_question")
    mock_aqt.gui_hooks.reviewer_did_show_answer = MockHook("reviewer_did_show_answer")
    mock_aqt.gui_hooks.reviewer_will_answer_card = MockHook("reviewer_will_answer_card")
    mock_aqt.gui_hooks.card_will_show = MockHook("card_will_show")
    mock_aqt.gui_hooks.main_window_did_init = MockHook("main_window_did_init")
    mock_aqt.gui_hooks.av_player_will_play = MockHook("av_player_will_play")
    mock_aqt.gui_hooks.reviewer_will_end = MockHook("reviewer_will_end")
    mock_aqt.gui_hooks.reviewer_did_answer_card = MockHook("reviewer_did_answer_card")
    mock_aqt.gui_hooks.theme_did_change = MockHook("theme_did_change")

    # Add general Anki hooks (not specific to GUI hooks)
    # Ankimon sometimes uses anki.hooks.addHook directly, so mock this as well.
    mock_anki.hooks.profile_did_open = MockHook("profile_did_open")
    mock_anki.hooks.profile_will_close = MockHook("profile_will_close")
    mock_anki.hooks.reviewer_did_show_question = MockHook("reviewer_did_show_question")
    mock_anki.hooks.reviewer_did_show_answer = MockHook("reviewer_did_show_answer")
    # Add other common anki.hooks as needed for Ankimon.


    # Mock Qt classes
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QMainWindow, QMenu, QMenuBar, QDialog, QVBoxLayout,
        QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy, QLineEdit, QCheckBox,
        QSpinBox, QDoubleSpinBox, QComboBox, QSlider, QListWidget, QListWidgetItem,
        QTabWidget, QTabBar, QToolButton, QDialogButtonBox, QTextEdit, QMessageBox, QScrollArea,
        QGridLayout, QTextBrowser, QToolBar, QStatusBar, QToolTip
    )
    from PyQt6.QtGui import (
        QAction, QKeySequence, QFont, QIcon, QColor, QPalette, QPixmap, QPainter, QMovie,
        QFontDatabase
    )
    from PyQt6.QtCore import Qt, QSize, QPoint, QRect, QTimer, pyqtSignal, QObject, QUrl, QFile

    # Assign all Qt classes to the mock aqt.qt module
    qt_classes = {
        'QApplication': QApplication, 'QWidget': QWidget, 'QMainWindow': QMainWindow, 'QMenu': QMenu,
        'QMenuBar': QMenuBar, 'QDialog': QDialog, 'QVBoxLayout': QVBoxLayout, 'QHBoxLayout': QHBoxLayout,
        'QLabel': QLabel, 'QPushButton': QPushButton, 'QFrame': QFrame, 'QKeySequence': QKeySequence,
        'QSizePolicy': QSizePolicy, 'QLineEdit': QLineEdit, 'QCheckBox': QCheckBox, 'QSpinBox': QSpinBox,
        'QDoubleSpinBox': QDoubleSpinBox, 'QComboBox': QComboBox, 'QSlider': QSlider, 'QListWidget': QListWidget,
        'QListWidgetItem': QListWidgetItem, 'QTabWidget': QTabWidget, 'QTabBar': QTabBar, 'QToolButton': QToolButton,
        'QDialogButtonBox': QDialogButtonBox, 'QTextEdit': QTextEdit, 'QMessageBox': QMessageBox,
        'QScrollArea': QScrollArea, 'QGridLayout': QGridLayout, 'QTextBrowser': QTextBrowser,
        'QAction': QAction, 'QFont': QFont, 'QFontDatabase': QFontDatabase, 'QIcon': QIcon, 'QColor': QColor,
        'QPalette': QPalette, 'QPixmap': QPixmap, 'QPainter': QPainter, 'QMovie': QMovie, 'Qt': Qt,
        'QSize': QSize, 'QPoint': QPoint, 'QRect': QRect, 'QTimer': QTimer, 'pyqtSignal': pyqtSignal,
        'QObject': QObject, 'qconnect': mock_qconnect, 'QToolBar': QToolBar, 'QStatusBar': QStatusBar,
        'QUrl': QUrl, 'QToolTip': QToolTip, 'QFile': QFile
    }
    for name, cls in qt_classes.items():
        setattr(mock_aqt.qt, name, cls)

    # Mock aqt.webview
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage
    mock_aqt.webview.AnkiWebView = QWebEngineView
    mock_aqt.webview.WebContent = MagicMock()


    # Mock aqt.sound
    class MockAVPlayer:
        def __init__(self):
            self.current_player = None
            self.no_interrupt = False
        def play_without_interrupt(self, file):
            print(f"MockAVPlayer: Playing {file} without interruption.")
        def stop(self):
            print("MockAVPlayer: Stopping current sound.")

    mock_aqt.sound.SoundOrVideoTag = lambda filename: {"filename": filename}
    mock_aqt.sound.AVPlayer = MockAVPlayer
    mock_aqt.sound.av_player = MockAVPlayer()

    # Mock aqt.toolbar
    mock_aqt.toolbar.Toolbar = QToolBar

    mock_aqt.theme.theme_manager = MagicMock()

    # Inject into sys.modules
    modules_to_inject = {
        "anki": mock_anki, "anki.collection": mock_anki.collection, "anki.cards": mock_anki.cards,
        "anki.notes": mock_anki.notes, "anki.sched": mock_anki.sched, "anki.utils": mock_anki.utils,
        "anki.hooks": mock_anki.hooks, "anki.buildinfo": mock_anki.buildinfo,
        "aqt": mock_aqt, "aqt.main": mock_aqt.main, "aqt.reviewer": mock_aqt.reviewer,
        "aqt.utils": mock_aqt.utils, "aqt.gui_hooks": mock_aqt.gui_hooks, "aqt.qt": mock_aqt.qt,
        "aqt.webview": mock_aqt.webview, "aqt.sound": mock_aqt.sound, "aqt.toolbar": mock_aqt.toolbar,
        "aqt.theme": mock_aqt.theme,
        "aqt.operations": mock_aqt.operations,
        "aqt.operations.scheduling": mock_aqt.operations.scheduling,
    }

    for module_name, module_obj in modules_to_inject.items():
        sys.modules[module_name] = module_obj

    print("Anki/AQT mocks injected into sys.modules")

def setup_global_mw():
    """Set up the global mw object that Ankimon expects"""
    from PyQt6.QtWidgets import QApplication
    from ankimon_test_env.mock_anki import MockAnkiMainWindow # Import our specific mock

    # Instantiate our custom MockAnkiMainWindow, passing the addon directory
    mw = MockAnkiMainWindow(addon_dir=str(ANKIMON_ADDON_DIR))
    
    # The form and reviewer of MockAnkiMainWindow are already set up correctly
    # We need to ensure the mw.form (which is the MockReviewerWindow) has access to mw
    # to correctly set up the reviewer itself. This is handled by passing self to MockReviewerWindow

    # The config.json loading for mw.addonManager.getConfig is handled internally by MockAddonManager
    # which is instantiated inside MockAnkiMainWindow using ANKIMON_ADDON_DIR.

    # Ensure mw.app is set, as Ankimon might expect it for global QApplication access
    mw.app = QApplication.instance() or QApplication(sys.argv)

    # Set in modules
    sys.modules['aqt'].mw = mw
    sys.modules['aqt.main'].mw = mw

    return mw

def create_mock_data_files():
    """Create necessary mock data files for Ankimon"""
    print("Creating mock data files...")
    ankimon_path = Path(__file__).parent.parent / "src" / "Ankimon"
    user_files_path = ankimon_path / "user_files"
    user_files_path.mkdir(parents=True, exist_ok=True)

    # List of files to create with default content
    # Create mock meta.json with default config
    meta_path = ankimon_path / "meta.json"
    if not meta_path.exists():
        mock_meta_content = {
            "config": {
                "gui.show_mainpkmn_in_reviewer": 2,
                "battle.hp_bar_thickness": 4,
                "gui.reviewer_image_gif": 1,
                "gui.reviewer_text_message_box": True,
                "misc.language": 9,
                "trainer.name": "TestTrainer",
                "trainer.sprite": "ash-sinnoh"
            }
        }
        with open(meta_path, 'w', encoding='utf-8') as f:
            json.dump(mock_meta_content, f, indent=2)
        print(f"Created mock meta.json: {meta_path}")

    # Copy data files from ResetFiles to user_files directory
    reset_files_path = project_root / "ResetFiles"
    files_to_copy = [
        "mypokemon.json",
        "mainpokemon.json",
        "itembag.json",
        "badges.json",
        "team.json",
    ]

    for filename in files_to_copy:
        src_path = reset_files_path / filename
        dest_path = user_files_path / filename
        if src_path.exists():
            # Always copy to ensure a clean state for each test run
            shutil.copy(src_path, dest_path)
            print(f"Copied '{filename}' from ResetFiles to user_files")
        else:
            print(f"Warning: '{filename}' not found in ResetFiles. A default empty file may be created if necessary.")

    # Now, create config.obf from the mock meta.json
    from Ankimon.pyobj.ankimon_sync import AnkimonDataSync
    sync_handler = AnkimonDataSync()
    sync_handler._save_obfuscated_config()
    print("Created mock config.obf from meta.json")


def load_ankimon_singletons():
    """Load and create all Ankimon singleton objects"""
    print("Loading Ankimon singletons...")
    try:
        src_path = Path(__file__).parent.parent / "src"
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))

        create_mock_data_files()

        # Now, import the singletons
        from Ankimon import singletons
        print("Successfully imported Ankimon.singletons")
        return {
            'settings_obj': singletons.settings_obj,
            'settings_window': singletons.settings_window,
            'translator': singletons.translator,
            'logger': singletons.logger,
            'main_pokemon': singletons.main_pokemon,
            'enemy_pokemon': singletons.enemy_pokemon,
            'trainer_card': singletons.trainer_card,
            'ankimon_tracker_obj': singletons.ankimon_tracker_obj,
            'test_window': singletons.test_window,
            'achievement_bag': singletons.achievement_bag,
            'data_handler_obj': singletons.data_handler_obj,
            'data_handler_window': singletons.data_handler_window,
            'shop_manager': singletons.shop_manager,
            'ankimon_tracker_window': singletons.ankimon_tracker_window,
            'pokedex_window': singletons.pokedex_window,
            'reviewer_obj': singletons.reviewer_obj,
            'eff_chart': singletons.eff_chart,
            'gen_id_chart': singletons.gen_id_chart,
            'license': singletons.license,
            'credits': singletons.credits,
            'version_dialog': singletons.version_dialog,
            'item_window': singletons.item_window,
            'pokecollection_win': singletons.pokecollection_win,
            'pokemon_pc': singletons.pokemon_pc,
        }

    except Exception as e:
        print(f"Error loading Ankimon singletons: {e}")
        import traceback
        traceback.print_exc()
        return None

def load_ankimon_menu(mw, ankimon_objects):
    """Load and initialize Ankimon menu"""
    print("Loading Ankimon menu...")
    try:
        from Ankimon.menu_buttons import create_menu_actions
        print("Successfully imported menu_buttons")

        create_menu_actions(
            database_complete=True,
            online_connectivity=False,
            pokecollection_win=ankimon_objects.get('pokecollection_win'),
            item_window=ankimon_objects.get('item_window'),
            test_window=ankimon_objects.get('test_window'),
            achievement_bag=ankimon_objects.get('achievement_bag'),
            open_team_builder=lambda: print("Mock callback: Team Builder"),
            export_to_pkmn_showdown=lambda: print("Mock callback: Export to Showdown"),
            export_all_pkmn_showdown=lambda: print("Mock callback: Export All to Showdown"),
            flex_pokemon_collection=lambda: print("Mock callback: Flex Collection"),
            eff_chart=ankimon_objects.get('eff_chart'),
            gen_id_chart=ankimon_objects.get('gen_id_chart'),
            credits=ankimon_objects.get('credits'),
            license=ankimon_objects.get('license'),
            open_help_window=lambda connectivity: print("Help window opened"),
            report_bug=lambda: print("Mock callback: Bug Report"),
            rate_addon_url=lambda: print("Mock callback: Rate Addon"),
            version_dialog=ankimon_objects.get('version_dialog'),
            trainer_card=ankimon_objects.get('trainer_card'),
            ankimon_tracker_window=ankimon_objects.get('ankimon_tracker_window'),
            logger=ankimon_objects.get('logger'),
            data_handler_window=ankimon_objects.get('data_handler_window'),
            settings_window=ankimon_objects.get('settings_window'), # Pass the real settings_window here
            shop_manager=ankimon_objects.get('shop_manager'),
            pokedex_window=ankimon_objects.get('pokedex_window'),
            ankimon_key='Ctrl+K',
            join_discord_url=lambda: print("Mock callback: Join Discord"),
            open_leaderboard_url=lambda: print("Mock callback: Open Leaderboard"),
            settings_obj=ankimon_objects.get('settings_obj'),
            addon_dir=Path(__file__).parent.parent / "src" / "Ankimon",
            data_handler_obj=ankimon_objects.get('data_handler_obj'),
            pokemon_pc=ankimon_objects.get('pokemon_pc'),
        )
        print("Ankimon menu actions created successfully")

    except Exception as e:
        print(f"Error loading Ankimon menu: {e}")
        import traceback
        traceback.print_exc()

from test_runner import TestRunnerGUI
from PyQt6.QtWidgets import QMainWindow, QMenuBar, QStatusBar, QTabWidget, QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QTextEdit

class MainApplicationWindow(QMainWindow):
    def __init__(self, ankimon_objects):
        super().__init__()
        self.ankimon_objects = ankimon_objects
        self.setWindowTitle("Ankimon Test Environment")
        self.setGeometry(100, 100, 1280, 720)
        self.setMenuBar(QMenuBar(self))
        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self.init_tabs()
        print("MainApplicationWindow initialized")

    def init_tabs(self):
        self.test_launcher_tab = TestRunnerGUI()
        self.tabs.addTab(self.test_launcher_tab, "Test Launcher")
        self.reviewer_tab = QWidget()
        self.init_reviewer_tab()
        self.tabs.addTab(self.reviewer_tab, "Simulated Reviewer")
        self.config_editor_tab = QTextEdit()
        self.tabs.addTab(self.config_editor_tab, "Config Editor")
        self.log_viewer_tab = QTextEdit()
        self.log_viewer_tab.setReadOnly(True)
        self.tabs.addTab(self.log_viewer_tab, "Log Viewer")

    def init_reviewer_tab(self):
        layout = QHBoxLayout(self.reviewer_tab)
        control_panel = QWidget()
        control_panel.setFixedWidth(300)
        control_layout = QVBoxLayout(control_panel)
        self.start_btn = QPushButton("Start Review")
        self.next_btn = QPushButton("Next Card")
        self.hud_btn = QPushButton("Show Ankimon HUD")
        self.answer_btn = QPushButton("Show Answer")
        control_layout.addWidget(self.start_btn)
        control_layout.addWidget(self.next_btn)
        control_layout.addWidget(self.hud_btn)
        control_layout.addWidget(self.answer_btn)
        ease_layout = QHBoxLayout()
        self.ease_btns = []
        for i, label in enumerate(["Again", "Hard", "Good", "Easy"], 1):
            btn = QPushButton(label)
            ease_layout.addWidget(btn)
            self.ease_btns.append(btn)
        control_layout.addLayout(ease_layout)
        control_layout.addStretch()
        self.reviewer_container = QWidget()
        self.reviewer_layout = QVBoxLayout(self.reviewer_container)
        layout.addWidget(control_panel)
        layout.addWidget(self.reviewer_container, 1)

    def setup_reviewer(self, reviewer):
        self.reviewer_layout.addWidget(reviewer.web.qwebengine_view)
        reviewer.bottom.web.qwebengine_view.setMaximumHeight(100)
        self.reviewer_layout.addWidget(reviewer.bottom.web.qwebengine_view)
        self.start_btn.clicked.connect(reviewer.show)
        self.next_btn.clicked.connect(reviewer.nextCard)
        self.answer_btn.clicked.connect(reviewer._showAnswer)
        for i, btn in enumerate(self.ease_btns, 1):
            btn.clicked.connect(lambda checked, ease=i: reviewer._answerCard(ease))
        print("Reviewer setup in tab complete")

def main():
    print("=== Ankimon Test Environment Starting ===")
    # Add src to sys.path early
    src_path = Path(__file__).parent.parent / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))

    # Mocks must be set up before QApplication is instantiated
    setup_anki_mocks()
    from PyQt6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    mw = setup_global_mw()
    ankimon_objects = load_ankimon_singletons()
    if not ankimon_objects:
        print("Failed to load Ankimon objects, exiting.")
        sys.exit(1)

    main_window = MainApplicationWindow(ankimon_objects)
    mw.form = main_window

    # Setup reviewer
    from mock_aqt.reviewer import EnhancedMockReviewer
    from mock_anki.collection import MockScheduler
    reviewer = EnhancedMockReviewer(mw, main_window)
    mw.reviewer = reviewer
    mw.col.sched = MockScheduler(mw)
    main_window.setup_reviewer(reviewer)

    # Load menu
    load_ankimon_menu(mw, ankimon_objects)
    if hasattr(mw, 'pokemenu') and mw.pokemenu:
        main_window.menuBar().addMenu(mw.pokemenu)
        print("Ankimon menu added to menubar")

    main_window.show()
    print("\n=== Ankimon Test Environment Ready ===")
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
