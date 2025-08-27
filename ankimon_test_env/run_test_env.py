import sys
import os
import types
import json
import base64
import shutil
import atexit
import glob
from pathlib import Path

# --- PyQt6 Imports ---
# Ensure a consistent import order for Qt components
try:
    from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton, QMainWindow, QMenuBar, QMenu, QDialog, QGridLayout, QFrame, QHBoxLayout
    from PyQt6.QtGui import QAction, QKeySequence, QPixmap, QFont, QFontDatabase, QGuiApplication
    from PyQt6.QtCore import Qt, QUrl
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    print("Successfully imported necessary PyQt6 components.")
except ImportError as e:
    print(f"Fatal Error: Could not import PyQt6 components. Please ensure PyQt6 and PyQt6-WebEngine are installed. Details: {e}")
    sys.exit(1)

# --- Add Ankimon to Python Path ---
ANKIMON_ROOT = Path(__file__).parent.parent.resolve()
sys.path.insert(0, str(ANKIMON_ROOT))
src_path = ANKIMON_ROOT / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# --- Backup and Restore Logic ---
BACKUP_DIR = Path(__file__).parent / "temp_config_backup"

def create_backup():
    """
    Creates a backup of user configuration files.
    This function is called at the start of the test environment.
    """
    try:
        if BACKUP_DIR.exists():
            shutil.rmtree(BACKUP_DIR)
        BACKUP_DIR.mkdir()

        user_files_path = ANKIMON_ROOT / "src" / "Ankimon" / "user_files"
        files_to_back_up = glob.glob(str(user_files_path / "*.json"))
        files_to_back_up += glob.glob(str(user_files_path / "*.obf"))

        meta_json_path = ANKIMON_ROOT / "src" / "Ankimon" / "meta.json"
        if meta_json_path.exists():
            files_to_back_up.append(str(meta_json_path))

        for f_path in files_to_back_up:
            shutil.copy(f_path, BACKUP_DIR)
        
        print(f"[BACKUP] Created backup of {len(files_to_back_up)} files in {BACKUP_DIR}")
    except Exception as e:
        print(f"[BACKUP] Error creating backup: {e}")

def restore_backup():
    """
    Restores user configuration files from the backup.
    This function is called at the end of the test environment session.
    """
    try:
        if not BACKUP_DIR.exists():
            return

        user_files_path = ANKIMON_ROOT / "src" / "Ankimon" / "user_files"
        backed_up_files = list(BACKUP_DIR.iterdir())
        
        for f_path in backed_up_files:
            if f_path.name == "meta.json":
                shutil.copy(f_path, ANKIMON_ROOT / "src" / "Ankimon" / "meta.json")
            else:
                shutil.copy(f_path, user_files_path / f_path.name)

        shutil.rmtree(BACKUP_DIR)
        print(f"[BACKUP] Restored {len(backed_up_files)} files and cleaned up backup directory.")
    except Exception as e:
        print(f"[BACKUP] Error restoring backup: {e}")

# --- Comprehensive Mocking Framework for Anki/AQT ---

def setup_ankiaqt_mocks():
    """
    Creates and injects a complete mock of the anki and aqt packages into sys.modules
    to prevent ImportErrors during testing.
    """
    print("--- Setting up Anki/AQT Mocking Framework ---")

    # --- Generic Mocking Utilities ---

    class DummyCallable:
        """A callable object that accepts any arguments and does nothing, returning itself."""
        def __call__(self, *args, **kwargs):
            return self
        def __getattr__(self, name):
            if name.startswith("__"):
                raise AttributeError
            return DummyCallable()

    class MockHook:
        """A mock for Anki/AQT hooks. Supports append, remove, and being called."""
        def __init__(self, name=""):
            self._name = name
            self._handlers = []
        def append(self, func):
            self._handlers.append(func)
        def remove(self, func):
            if func in self._handlers:
                self._handlers.remove(func)
        def __call__(self, *args, **kwargs):
            if "will" in self._name or "filter" in self._name:
                if args:
                    return args[0]
            for handler in self._handlers:
                try:
                    handler(*args, **kwargs)
                except Exception as e:
                    print(f"[MOCK Hook '{self._name}'] Error in handler {handler.__name__}: {e}")

    class MockModule(types.ModuleType):
        """A module that returns a DummyCallable for any attribute that is not found."""
        def __getattr__(self, name):
            if name.startswith("__"):
                raise AttributeError
            setattr(self, name, DummyCallable())
            return getattr(self, name)

    # --- Specific Mock Implementations ---

    class MockAddonManager:
        _OBFUSCATION_KEY = "H0tP-!s-N0t-4-C@tG!rL_v2"

        def __init__(self, addon_path):
            self.addon_path = Path(addon_path)

        def _deobfuscate_data(self, obfuscated_str: str) -> dict:
            separator = "---DATA_START---" + "\n"
            parts = obfuscated_str.split(separator)
            obfuscated_data = parts[1] if len(parts) > 1 else parts[0]
            obfuscated_bytes = base64.b64decode(obfuscated_data)
            deobfuscated_bytes = bytearray()
            key_bytes = self._OBFUSCATION_KEY.encode('utf-8')
            for i, byte in enumerate(obfuscated_bytes):
                deobfuscated_bytes.append(byte ^ key_bytes[i % len(key_bytes)])
            return json.loads(deobfuscated_bytes.decode('utf-8'))

        def getConfig(self, module_name):
            config = {}
            default_config_path = self.addon_path / 'src' / 'Ankimon' / 'config.json'
            if default_config_path.exists():
                with open(default_config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            
            user_config_path = self.addon_path / 'src' / 'Ankimon' / 'user_files' / 'config.obf'
            if user_config_path.exists():
                try:
                    with open(user_config_path, 'r', encoding='utf-8') as f:
                        obfuscated_str = f.read()
                    if obfuscated_str:
                        user_config = self._deobfuscate_data(obfuscated_str)
                        config.update(user_config)
                except Exception as e:
                    print(f"[MOCK] Could not load or deobfuscate config.obf: {e}")

            return config

        def setWebExports(self, module, pattern):
            pass
        def addonFromModule(self, module):
            return "ankimon_mock_package"
        def writeConfig(self, module, config):
            pass

    # --- Mock Card and Scheduler for Reviewer ---
    class MockCard:
        def __init__(self, question, answer):
            self._question = question
            self._answer = answer
        def question(self):
            return self._question
        def answer(self):
            return self._answer
        def time_taken(self): # Reviewer might access card.time_taken
            return 1000 # Dummy value
        def note(self): # Reviewer might access card.note
            return DummyCallable()
        def current_deck_id(self): # Reviewer might access card.current_deck_id
            return 1 # Dummy value

    class MockScheduler:
        def __init__(self, mw_instance): # Accept mw_instance
            self.mw = mw_instance # Store mw_instance
            self.cards = [
                MockCard("What is the capital of Japan?", "Tokyo"),
                MockCard("What is the highest mountain in the world?", "Mount Everest"),
                MockCard("What is the largest ocean?", "Pacific Ocean"),
            ]
            self.current_card_index = -1

        def get_next_card(self):
            self.current_card_index += 1
            if self.current_card_index < len(self.cards):
                return self.cards[self.current_card_index]
            else:
                print("[MOCK Scheduler] No more cards in the queue.")
                return None

        def startReview(self):
            print("[MOCK Scheduler] startReview() called.")
            card = self.get_next_card()
            if card:
                self.mw.reviewer._showQuestion(card) # Use self.mw
            else:
                self.mw.reviewer.web.setHtml("<h1>Review complete!</h1>") # Use self.mw

        def answerButtons(self, card): # Used in __init__.py
            return 4 # Simulate 4 ease buttons

    # --- Mock 'anki' package ---
    anki = MockModule('anki')
    anki.__path__ = []
    sys.modules['anki'] = anki
    
    anki_hooks = MockModule('anki.hooks')
    anki_hooks.addHook = MockHook("addHook_global")
    anki_hooks.remHook = MockHook("remHook_global")
    anki_hooks.runHook = MockHook("runHook_global")
    anki_hooks.runFilter = lambda _filter, val, *args: val
    anki_hooks.wrap = lambda old, new, pos: new
    sys.modules['anki.hooks'] = anki_hooks
    anki.hooks = anki_hooks

    anki_utils = MockModule("anki.utils")
    anki_utils.is_win = sys.platform == "win32"
    anki_utils.isWin = anki_utils.is_win
    sys.modules['anki.utils'] = anki_utils
    anki.utils = anki_utils

    anki_buildinfo = MockModule("anki.buildinfo")
    anki_buildinfo.version = "2.1.99"
    sys.modules['anki.buildinfo'] = anki_buildinfo
    anki.buildinfo = anki_buildinfo

    # --- Mock 'aqt' package ---
    aqt = MockModule('aqt')
    aqt.__path__ = []
    sys.modules['aqt'] = aqt
    aqt.QWebEngineView = QWebEngineView
    aqt.QDialog = QDialog
    aqt.QVBoxLayout = QVBoxLayout
    aqt.QPixmap = QPixmap
    aqt.QGridLayout = QGridLayout

    # Mock 'aqt.qt'
    aqt_qt = MockModule('aqt.qt')
    aqt_qt.QAction, aqt_qt.QMenu, aqt_qt.QKeySequence = QAction, QMenu, QKeySequence
    aqt_qt.QWidget, aqt_qt.QVBoxLayout, aqt_qt.QLabel = QWidget, QVBoxLayout, QLabel
    aqt_qt.QPushButton, aqt_qt.QMainWindow, aqt_qt.QMenuBar = QPushButton, QMainWindow, QMenuBar
    aqt_qt.QDialog, aqt_qt.Qt, aqt_qt.QFile, aqt_qt.QUrl, aqt_qt.QFrame = QDialog, Qt, DummyCallable, QUrl, QFrame
    aqt_qt.QPixmap = QPixmap
    aqt_qt.QGridLayout = QGridLayout
    aqt_qt.QHBoxLayout = QHBoxLayout
    aqt_qt.QFont = QFont
    aqt_qt.QFontDatabase = QFontDatabase
    aqt_qt.QSizePolicy = DummyCallable
    aqt_qt.QMessageBox = DummyCallable
    aqt_qt.QToolTip = DummyCallable
    sys.modules['aqt.qt'] = aqt_qt
    aqt.qt = aqt_qt

    # Mock 'aqt.utils'
    aqt_utils = MockModule('aqt.utils')
    aqt_utils.showWarning = lambda text, **kwargs: print(f"[MOCK showWarning] {text}")
    aqt_utils.showInfo = lambda text, **kwargs: print(f"[MOCK showInfo] {text}")
    aqt_utils.showCritical = lambda text, **kwargs: print(f"[MOCK showCritical] {text}")
    aqt_utils.tooltip = lambda text, **kwargs: print(f"[MOCK tooltip] {text}")
    aqt_utils.qconnect = lambda signal, slot: signal.connect(slot)
    aqt_utils.downArrow = lambda: "▼"
    aqt_utils.tr = lambda text, *args, **kwargs: text
    aqt_utils.QWebEngineSettings = QWebEngineSettings
    aqt_utils.QWebEnginePage = QWebEnginePage
    aqt_utils.QWebEngineView = QWebEngineView
    sys.modules['aqt.utils'] = aqt_utils
    aqt.utils = aqt_utils

    # Mock 'aqt.gui_hooks'
    aqt_gui_hooks = MockModule('aqt.gui_hooks')
    for hook_name in ["reviewer_will_show_question", "reviewer_did_show_answer", "editor_did_init_note", "editor_did_load_note", "deck_browser_did_render", "profile_did_open", "profile_will_close", "collection_did_flush", "add_cards_did_add_note", "webview_will_set_content", "reviewer_will_answer_card", "reviewer_did_answer_card", "sync_did_finish", "reviewer_will_end", "sync_will_start", "theme_did_change"]:
        setattr(aqt_gui_hooks, hook_name, MockHook(hook_name))
    sys.modules['aqt.gui_hooks'] = aqt_gui_hooks
    aqt.gui_hooks = aqt_gui_hooks

    # Mock 'aqt.reviewer'
    aqt_reviewer = MockModule('aqt.reviewer')
    class MockReviewer:
        def __init__(self, parent=None):
            self.card = None
            self.web = QWebEngineView(parent)
            # Set the base URL for resolving relative paths to assets
            self.web_assets_path = QUrl.fromLocalFile("C:/Users/kuri-chan/Documents/ankimon/src/Ankimon/aqt/data/web/")
            self.web.setHtml("<h1>Mock Reviewer: No card loaded.</h1>", self.web_assets_path)
            self.web.hide()

        def _shortcutKeys(self):
            return []
        
        def _linkHandler(self, *args):
            print(f"[MOCK Reviewer] _linkHandler called with: {args}")
            if self.card:
                self._showAnswer(self.card)

        def _showQuestion(self, card):
            self.card = card
            html_content = f"""
            <html>
            <head>
                <link rel="stylesheet" type="text/css" href="dist/reviewer-bottom.css">
                <script src="dist/reviewer-bottom.js"></script>
                <style>
                    /* Basic styles for mock, will be overridden by Anki's CSS */
                    body {{ font-family: sans-serif; font-size: 20px; text-align: center; }}
                    .card {{ background-color: #f0f0f0; padding: 20px; border-radius: 10px; }}
                    .question {{ color: #333; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="question">{card.question()}</div>
                </div>
            </body>
            </html>
            """
            self.web.setHtml(html_content, self.web_assets_path)
            self.web.show()

        def _showAnswer(self, card):
            html_content = f"""
            <html>
            <head>
                <link rel="stylesheet" type="text/css" href="dist/reviewer-bottom.css">
                <script src="dist/reviewer-bottom.js"></script>
                <style>
                    /* Basic styles for mock, will be overridden by Anki's CSS */
                    body {{ font-family: sans-serif; font-size: 20px; text-align: center; }}
                    .card {{ background-color: #e0e0e0; padding: 20px; border-radius: 10px; }}
                    .question {{ color: #333; }}
                    .answer {{ color: #007bff; margin-top: 15px; }}
                </style>
            </head>
            <body>
                <div class="card">
                    <div class="question">{card.question()}</div>
                    <hr>
                    <div class="answer">{card.answer()}</div>
                    <button onclick="pycmd('ease1')">Again</button>
                    <button onclick="pycmd('ease2')">Hard</button>
                    <button onclick="pycmd('ease3')">Good</button>
                    <button onclick="pycmd('ease4')">Easy</button>
                </div>
            </body>
            </html>
            """
            self.web.setHtml(html_content, self.web_assets_path)
            self.web.show()

        def show(self):
            print("[MOCK Reviewer] show() called. Webview should be visible.")
            self.web.show()

    aqt_reviewer.Reviewer = MockReviewer
    sys.modules['aqt.reviewer'] = aqt_reviewer
    aqt.reviewer = aqt_reviewer
    
    # Mock 'aqt.webview'
    aqt_webview = MockModule("aqt.webview")
    class MockWebContent:
        def __init__(self, *args, **kwargs):
            self.js = []
            self.body = ""
    aqt_webview.WebContent = MockWebContent
    sys.modules['aqt.webview'] = aqt_webview
    aqt.webview = aqt_webview

    # Mock 'aqt.sound'
    aqt_sound = MockModule("aqt.sound")
    aqt_sound.av_player = DummyCallable()
    aqt_sound.SoundOrVideoTag = type('SoundOrVideoTag', (object,), {})
    aqt_sound.AVPlayer = type('AVPlayer', (object,), {})
    sys.modules['aqt.sound'] = aqt_sound
    aqt.sound = aqt_sound

    # Mock 'aqt.theme'
    aqt_theme = MockModule("aqt.theme")
    aqt_theme.theme_manager = DummyCallable()
    sys.modules['aqt.theme'] = aqt_theme
    aqt.theme = aqt_theme

    # Mock 'aqt.main' and 'aqt.mw' (the main window)
    class MockMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.mw = self
            self.form = QWidget()
            self.setCentralWidget(self.form)
            self.form.vbox = QVBoxLayout(self.form)

            self.col = DummyCallable()
            self.col.conf = {}
            self.col.sched = MockScheduler(self.mw)

            self.reviewer = MockReviewer(parent=self.form) # Pass form as parent
            self.form.vbox.addWidget(self.reviewer.web) # Add reviewer's webview to main window layout

            self.addonManager = MockAddonManager(ANKIMON_ROOT)
            self.pm = DummyCallable()
            self.pm.name = "test-profile"
            self.menubar = self.menuBar()
            self.form.menubar = self.menubar
            self.pokemenu = QMenu("Ankimon (Mock)", self)
            self.menubar.addMenu(self.pokemenu)
            start_review_action = QAction("Start Review (Mock)", self)
            start_review_action.triggered.connect(self._start_mock_review)
            self.pokemenu.addAction(start_review_action)

        def _start_mock_review(self):
            print("Starting mock review!")
            # Hide other widgets if any, and show reviewer's webview
            # For now, just ensure reviewer's webview is visible
            self.reviewer.web.show()
            # Trigger the scheduler to get a card
            self.col.sched.startReview()

        def __getattr__(self, name):
            if name.startswith("__"):
                raise AttributeError
            return DummyCallable()

    aqt.mw = MockMainWindow()
    
    for submodule in ['addons', 'browser', 'editor', 'deckbrowser']:
        full_module_name = f'aqt.{submodule}'
        if full_module_name not in sys.modules:
            mod = MockModule(full_module_name)
            sys.modules[full_module_name] = mod
            setattr(aqt, submodule, mod)

    print("--- Anki/AQT Mocking Framework is LIVE ---")
    return aqt.mw

# --- Main Test Environment ---

def run_test_environment():
    """
    Sets up and runs the Ankimon test environment.
    """
    print("\n--- Starting Ankimon Test Environment ---")

    atexit.register(restore_backup)
    create_backup()

    mw = setup_ankiaqt_mocks()

    print("\n--- Importing Ankimon Modules ---")
    try:
        import Ankimon
        print("Successfully imported Ankimon package.")
        ANKIMON_AVAILABLE = True
    except Exception as e:
        print(f"FATAL: Failed to import Ankimon modules even with mocks. Error: {e}")
        import traceback
        traceback.print_exc()
        ANKIMON_AVAILABLE = False
        mw.show()
        return

    if ANKIMON_AVAILABLE:
        print("\n--- Ankimon Menu Should Be Populated ---")
        if mw.pokemenu.actions():
            print(f"Successfully populated Ankimon menu with {len(mw.pokemenu.actions())} actions.")
        else:
            print("Warning: Ankimon menu was not populated.")
            label = QLabel("Ankimon imported, but menu is empty.")
            mw.form.vbox.addWidget(label)
    else:
        label = QLabel("Ankimon modules failed to import. Cannot create menu.")
        mw.form.vbox.addWidget(label)

    mw.setWindowTitle("Ankimon Test Environment")
    mw.setGeometry(100, 100, 600, 400)
    mw.show()
    print("\n--- Test Environment Setup Complete. Mock window is now showing. ---")


if __name__ == '__main__':
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    run_test_environment()

    print("Starting Qt event loop...")
    sys.exit(app.exec())
