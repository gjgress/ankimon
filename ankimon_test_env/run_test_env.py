import sys
import os
import argparse
import json
import logging
import tempfile
import io
from pathlib import Path
from types import ModuleType
import importlib.util

# --- Global Variables for Test Environment ---
app = None  # Global QApplication instance or dummy
is_headless_env = True  # Flag indicating if we are running without full PyQt6 GUI
is_headless_file_mode = False # Flag for specific file testing in headless mode
mw_instance = None # Global instance for MockMainWindow

# --- Argument Parsing ---
parser = argparse.ArgumentParser(description="Enhanced Ankimon Test Environment")
parser.add_argument('--file', type=str, help='Path to an individual Python file to test')
parser.add_argument('--full-anki', action='store_true', help='Run a full Anki-like interface with enhanced Ankimon menu and reviewer')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
parser.add_argument('--selftest', action='store_true', help='Run self-tests and exit')
parser.add_argument('--log-level', type=str, default='INFO', help='Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
args = parser.parse_args()

# --- Logging Configuration ---
# Configure logging early, before any potential errors occur
log_format = '%(asctime)s - %(levelname)s - %(name)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# Set logging level based on arguments
numeric_level = getattr(logging, args.log_level.upper(), None)
if not isinstance(numeric_level, int):
    logger.error(f"Invalid log level: '{args.log_level}'. Using INFO.")
    numeric_level = logging.INFO
if args.debug:
    numeric_level = max(numeric_level, logging.DEBUG) # Ensure debug is set if --debug is used
logger.setLevel(numeric_level)
logger.debug(f"Logging level set to: {logging.getLevelName(numeric_level)}")

# --- QApplication Instantiation ---
# This block attempts to import necessary Qt modules and create QApplication
# as early as possible to avoid 'QtWebEngineWidgets must be imported...' errors.
# If any imports fail, it falls back to headless mode with dummy classes.

# Only attempt GUI imports and QApplication if not explicitly a headless selftest
# or if a GUI mode (--full-anki or --file) is requested.
if not args.selftest or (args.selftest and not os.environ.get('ANKIMON_HEADLESS_SELFTEST', 'False') == 'True'):
    try:
        # Crucial: Import QtWebEngineWidgets related modules before QApplication
        # This order is important to prevent certain runtime errors.
        from PyQt6.QtWebEngineWidgets import QWebEngineView, QWebEnginePage, QWebEngineSettings
        from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSizePolicy, QGridLayout, QFrame, QToolTip, QMenuBar, QMenu, QCheckBox
        from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter, QFontDatabase, QAction
        from PyQt6.QtCore import Qt, QSize, QFile, QUrl, QTimer, QCoreApplication

        # Attempt to create QApplication instance
        if QApplication.instance():
            app = QApplication.instance()
            logger.debug("QApplication instance already exists, reusing.")
        else:
            app = QApplication(sys.argv)
            logger.debug("New QApplication instance created.")
        is_headless_env = False # GUI environment successfully set up

    except ImportError as e:
        logger.warning(f"PyQt6 or QtWebEngineWidgets not fully available: {e}. Falling back to headless operation for GUI components.")
        if args.full_anki and not args.selftest:
            logger.critical("Full Anki-like interface requires PyQt6 GUI but it's not available. Exiting.")
            sys.exit(1)
    except Exception as e:
        logger.warning(f"Unexpected error during PyQt6/QApplication setup: {type(e).__name__}: {e}. Falling back to headless operation.")
        if args.full_anki and not args.selftest:
            logger.critical("Full Anki-like interface requires PyQt6 GUI but it's not available. Exiting.")
            sys.exit(1)

# If GUI setup failed or was not intended, define dummy classes for GUI components
if is_headless_env:
    logger.debug("Defining dummy PyQt6 components for headless operation.")

    class DummyQApplication:
        def instance(self): return None
        def processEvents(self): pass
        def quit(self): pass
        def exec(self): return 0
    app = DummyQApplication() # Assign dummy app for consistent API

    class QMainWindow: pass
    class QMessageBox:
        def setText(self, text): pass
        def exec(self): pass
    class QDialog:
        def __init__(self, parent=None): pass
        def setWindowTitle(self, title): pass
        def setGeometry(self, *args): pass
        def setLayout(self, layout): pass
        def show(self): pass
        def exec(self): return 0
    class QWidget:
        def __init__(self, parent=None): pass
        def setWindowTitle(self, title): pass
        def setGeometry(self, *args): pass
        def setLayout(self, layout): pass
        def show(self): pass
    class QVBoxLayout:
        def __init__(self, parent=None): pass
        def addWidget(self, widget): pass
        def addLayout(self, layout): pass
    class QHBoxLayout:
        def __init__(self, parent=None): pass
        def addWidget(self, widget): pass
    class QAction:
        def __init__(self, text, parent=None):
            self.text = text
            self.parent = parent
            self._triggered_signal = MockSignal() # Instance of MockSignal
            logger.debug(f"Mock QAction initialized: '{self.text}'")
        @property
        def triggered(self):
            return self._triggered_signal
    class Qt:
        class SizeHint: pass
        AlignLeft = 0; AlignRight = 0; AlignCenter = 0; AlignTop = 0; AlignBottom = 0; TextWordWrap = 0
    class QSize: pass
    class QFile: pass
    class QUrl: pass
    class QTimer:
        @staticmethod
        def singleShot(ms, func): pass
    class QWebEngineSettings:
        def setFullScreenSupportEnabled(self, enabled): logger.debug(f"DummyQWebEngineSettings: setFullScreenSupportEnabled({enabled}) called.")
    class QWebEnginePage:
        def __init__(self): self._settings = QWebEngineSettings(); logger.debug("DummyQWebEnginePage initialized.")
        def settings(self): logger.debug("DummyQWebEnginePage: settings() called."); return self._settings
        def eval(self, js_code): logger.debug(f"DummyQWebEnginePage.eval called with: {js_code[:100]}...")
    class QWebEngineView(QWidget):
        def __init__(self): super().__init__(); self._page = QWebEnginePage()
        def page(self): return self._page
        def setHtml(self, html_content): logger.debug(f"DummyQWebEngineView.setHtml: {html_content[:100]}...")
        def setMinimumHeight(self, height): pass

# Determine if we are in headless file mode (no GUI for the webview).
# This flag is primarily used within setup_test_environment and other mocks.
is_headless_file_mode = is_headless_env or bool(args.file) or os.environ.get('ANKIMON_HEADLESS_SELFTEST', 'False') == 'True'

# Ensure consistency: if the app is a DummyQApplication, we are definitely headless.
if isinstance(app, DummyQApplication):
    is_headless_env = True
    is_headless_file_mode = True

# --- Custom Exceptions ---
class ConfigError(Exception):
    """Custom exception for errors related to Ankimon configuration loading."""
    pass

# --- Configuration Loading Helpers ---
def load_ankimon_json(file_name: Path):
    """Loads JSON data from Ankimon's user_files, logging errors."""
    base_path = Path(__file__).parent.parent / "src" / "Ankimon" / "user_files"
    file_path = base_path / file_name
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"ConfigError: JSON file not found: {file_path}")
        raise ConfigError(f"Required JSON file not found: {file_path}")
    except json.JSONDecodeError:
        logger.error(f"ConfigError: Error decoding JSON from file: {file_path}")
        raise ConfigError(f"Corrupt JSON in file: {file_path}")

def load_ankimon_config():
    """Loads Ankimon's config.json, logging errors."""
    config_path = Path(__file__).parent.parent / "src" / "Ankimon" / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.error(f"ConfigError: Ankimon config.json not found: {config_path}")
        raise ConfigError(f"Ankimon config.json not found: {config_path}")
    except json.JSONDecodeError:
        logger.error(f"ConfigError: Error decoding JSON from Ankimon config.json: {config_path}")
        raise ConfigError(f"Corrupt JSON in Ankimon config.json: {config_path}")

# --- Mock Classes ---
# These mocks are essential for running Ankimon logic without a full Anki installation.
# They are designed to mimic the behavior of Anki's internal objects and modules.

class MockSignal: # Minimal mock for signals
    def connect(self, slot): pass

class MockSettings:
    """Mock for Ankimon.pyobj.settings.Settings"""
    def __init__(self):
        try:
            self.config = load_ankimon_config()
            logger.debug("MockSettings initialized with loaded config.")
        except ConfigError as e:
            logger.warning(f"MockSettings: Failed to load config: {e}. Using default fallback.")
            self.config = { # Fallback config
                "misc.language": 9, "misc.discord_rich_presence": False, "battle.dmg_in_reviewer": True,
                "gui.review_hp_bar_thickness": 2, "gui.reviewer_text_message_box_time": 3,
                "gui.show_mainpkmn_in_reviewer": 1, "gui.xp_bar_location": 2, "misc.show_tip_on_startup": True
            }

    def get(self, key, default=None):
        keys = key.split('.')
        val = self.config
        try:
            for k in keys:
                val = val[k]
            return val
        except (KeyError, TypeError):
            logger.debug(f"MockSettings: Key '{key}' not found, returning default '{default}'.")
            return default

    def set(self, key, value):
        logger.debug(f"MockSettings: Set '{key}' to '{value}'. (Mocked)")

class MockTranslator:
    """Mock for Ankimon.pyobj.translator.Translator"""
    def __init__(self, language=9):
        self.language = language
        logger.debug(f"MockTranslator initialized with language {language}.")
    def translate(self, key, **kwargs):
        return f"Translated_{key}"

class MockShowInfoLogger:
    """Mock for Ankimon.pyobj.InfoLogger.ShowInfoLogger"""
    def __init__(self):
        logger.debug("MockShowInfoLogger initialized.")
    def log(self, *args, **kwargs):
        logger.info(f"MockLogger.log: {args}, {kwargs}")
    def log_and_showinfo(self, *args, **kwargs):
        logger.info(f"MockLogger.log_and_showinfo: {args}, {kwargs}")
    def toggle_log_window(self):
        logger.debug("MockLogger.toggle_log_window called")

class MockAddonManager:
    """Mocks Anki's addonManager object for config management."""
    def __init__(self):
        self._configs = {}
        try:
            ankimon_default_config = load_ankimon_config()
            self._configs["Ankimon.config_var"] = ankimon_default_config
        except ConfigError as e:
            logger.warning(f"MockAddonManager could not load Ankimon config: {e}. Using empty config.")
            self._configs["Ankimon.config_var"] = {}
        logger.debug(f"MockAddonManager.__init__: Initialized _configs: {self._configs}")
        self.addonsFolder = Path(__file__).parent.parent / "src" / "Ankimon"

    def getConfig(self, name):
        logger.debug(f"MockAddonManager.getConfig: Called for {name}.")
        return self._configs.get(name, {})

    def writeConfig(self, name, config):
        logger.debug(f"MockAddonManager.writeConfig: Called for {name}.")
        current_config = self._configs.get(name, {})
        current_config.update(config)
        self._configs[name] = current_config

    def setWebExports(self, name, pattern): logger.debug(f"setWebExports called: {name}, {pattern}")
    def addonFromModule(self, name): return "Ankimon"

class MockCard:
    """Mocks an Anki Card object."""
    def __init__(self, card_id, question="Sample Question", answer="Sample Answer", note_type="Basic"):
        self.id = card_id; self.question = question; self.answer = answer; self.note_type = note_type
        self.queue = 0; self.type = 0; self.due = 1; self.ivl = 0; self.factor = 2500
        self.reps = 0; self.lapses = 0; self.left = 0; self.odue = 0; self.odid = 0
        self.flags = 0; self.data = ""
    def q(self): return f"<div class='card'><h2>{self.question}</h2></div>"
    def a(self): return f"<div class='card'><h2>{self.question}</h2><hr><p>{self.answer}</p></div>"

class PureMockQWebEngineSettings:
    """Pure Python mock for QWebEngineSettings."""
    def __init__(self): logger.debug("PureMockQWebEngineSettings initialized.")
    def setFullScreenSupportEnabled(self, enabled): logger.debug(f"PureMockQWebEngineSettings: setFullScreenSupportEnabled({enabled}) called.")

class PureMockQWebEnginePage:
    """Pure Python mock for QWebEnginePage."""
    def __init__(self):
        logger.debug("PureMockQWebEnginePage initialized.")
        self._settings = PureMockQWebEngineSettings()
    def settings(self):
        logger.debug("PureMockQWebEnginePage: settings() called.")
        return self._settings
    def eval(self, js_code):
        logger.debug(f"PureMockQWebEnginePage.eval called with: {js_code[:100]}...")

class PureMockQWebEngineView:
    """Pure Python mock for QWebEngineView."""
    def __init__(self):
        logger.debug("PureMockQWebEngineView initialized.")
        self._page = PureMockQWebEnginePage()
    def page(self):
        logger.debug("PureMockQWebEngineView: page() called.")
        return self._page
    def setHtml(self, html_content):
        logger.debug(f"PureMockQWebEngineView.setHtml called with: {html_content[:100]}...")
    def setMinimumHeight(self, height): pass

class MockReviewerWindow(QDialog):
    """Mock Anki reviewer window with card simulation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mock Anki Reviewer")
        self.setGeometry(200, 200, 800, 600)
        self.layout = QVBoxLayout(self)

        self.web = PureMockQWebEngineView() if is_headless_file_mode else QWebEngineView()
        self.web.setMinimumHeight(400)
        self.layout.addWidget(self.web)

        self.answer_buttons_layout = QHBoxLayout()
        self.again_btn = QPushButton("Again (1)"); self.hard_btn = QPushButton("Hard (2)"); self.good_btn = QPushButton("Good (3)"); self.easy_btn = QPushButton("Easy (4)")
        for btn in [self.again_btn, self.hard_btn, self.good_btn, self.easy_btn]:
            btn.setMinimumHeight(40)
        self.answer_buttons_layout.addWidget(self.again_btn); self.answer_buttons_layout.addWidget(self.hard_btn); self.answer_buttons_layout.addWidget(self.good_btn); self.answer_buttons_layout.addWidget(self.easy_btn)
        self.layout.addLayout(self.answer_buttons_layout)

        self.again_btn.clicked.connect(lambda: self.answer_card(1))
        self.hard_btn.clicked.connect(lambda: self.answer_card(2))
        self.good_btn.clicked.connect(lambda: self.answer_card(3))
        self.easy_btn.clicked.connect(lambda: self.answer_card(4))

        self.show_answer_btn = QPushButton("Show Answer")
        self.show_answer_btn.setMinimumHeight(40)
        self.show_answer_btn.clicked.connect(self.show_answer)
        self.layout.addWidget(self.show_answer_btn)

        self.current_card_index = 0
        self.showing_answer = False
        self.cards = [MockCard(i) for i in range(1, 6)] # Sample cards

        self.hide_answer_buttons()
        self.load_current_card()

    def hide_answer_buttons(self):
        for btn in [self.again_btn, self.hard_btn, self.good_btn, self.easy_btn]: btn.hide()
        self.show_answer_btn.show()

    def show_answer_buttons(self):
        for btn in [self.again_btn, self.hard_btn, self.good_btn, self.easy_btn]: btn.show()
        self.show_answer_btn.hide()

    def load_current_card(self):
        if self.current_card_index < len(self.cards):
            card = self.cards[self.current_card_index]
            self.current_card = card
            self.showing_answer = False
            html_content = f"<!DOCTYPE html><html><head><style>body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }} .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }} h2 {{ color: #333; margin-top: 0; }} hr {{ border: none; border-top: 2px solid #ddd; margin: 20px 0; }} p {{ font-size: 16px; line-height: 1.5; }} .card-info {{ font-size: 12px; color: #666; margin-top: 15px; }}</style></head><body>{card.q()}<div class='card-info'>Card {self.current_card_index + 1} of {len(self.cards)} | Type: {card.note_type}</div></body></html>"
            self.web.setHtml(html_content)
            self.hide_answer_buttons()
            # Trigger reviewer_did_show_question hook
            if 'mock_aqt_gui_hooks_module' in globals():
                for func in mock_aqt_gui_hooks_module.reviewer_did_show_question: func(card)
        else:
            self.web.setHtml("<div class='card'><h2>No more cards!</h2><p>Review session complete.</p></div>")
            self.show_answer_btn.hide()

    def show_answer(self):
        if hasattr(self, 'current_card') and not self.showing_answer:
            card = self.current_card
            self.showing_answer = True
            html_content = f"<!DOCTYPE html><html><head><style>body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }} .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }} h2 {{ color: #333; margin-top: 0; }} hr {{ border: none; border-top: 2px solid #ddd; margin: 20px 0; }} p {{ font-size: 16px; line-height: 1.5; }} .card-info {{ font-size: 12px; color: #666; margin-top: 15px; }}</style></head><body>{card.a()}<div class='card-info'>Card {self.current_card_index + 1} of {len(self.cards)} | Type: {card.note_type}</div></body></html>"
            self.web.setHtml(html_content)
            self.show_answer_buttons()
            # Trigger reviewer_did_show_answer hook
            if 'mock_aqt_gui_hooks_module' in globals():
                for func in mock_aqt_gui_hooks_module.reviewer_did_show_answer: func(card)

    def answer_card(self, ease):
        if hasattr(self, 'current_card'):
            card = self.current_card
            logger.debug(f"Card {card.id} answered with ease: {ease}")
            # Trigger reviewer_did_answer_card hook
            if 'mock_aqt_gui_hooks_module' in globals():
                for func in mock_aqt_gui_hooks_module.reviewer_did_answer_card: func(None, card, ease)
            self.current_card_index += 1
            if hasattr(QTimer, 'singleShot'): QTimer.singleShot(300, self.load_current_card)

class MockCollection: """Mocks Anki's Collection object."""
class MockAnkiHooks:
    """Mocks Anki's hooks module."""
    def addHook(self, *args, **kwargs): pass
    def wrap(self, *args, **kwargs):
        def decorator(func): return func
        return decorator

class MockGuiHooks:
    """Mocks Anki's gui_hooks module."""
    def __init__(self):
        self.reviewer_will_end = []; self.reviewer_did_answer_card = []; self.theme_did_change = []
        self.reviewer_did_show_question = []; self.reviewer_did_show_answer = []; self.webview_will_set_content = []
        self.addon_config_editor_will_display_json = []; self.reviewer_will_answer_card = []; self.profile_did_open = []
    def addHook(self, *args, **kwargs): pass

class MockQWebEngineSettings: """Basic mock for QWebEngineSettings."""
class MockQWebEnginePage:
    def __init__(self): pass
    def eval(self, js_code): logger.debug(f"MockQWebEnginePage.eval called with: {js_code[:100]}...")

class MockUtils:
    """Mocks Anki's utils module."""
    def downArrow(self, *args, **kwargs): pass
    def showWarning(self, *args, **kwargs): logger.debug(f"showWarning called: {args}")
    def showInfo(self, *args, **kwargs): logger.debug(f"showInfo called: {args}")
    def tr(self, *args, **kwargs): return args[0] if args else ""
    def tooltip(self, *args, **kwargs): logger.debug(f"tooltip called: {args}")
    def qconnect(self, *args, **kwargs): logger.debug(f"qconnect called: {args}")
    def QWebEngineSettings(self, *args, **kwargs): return MockQWebEngineSettings()
    def QWebEnginePage(self, *args, **kwargs): return MockQWebEnginePage()
    def QWebEngineView(self, *args, **kwargs): return PureMockQWebEngineView() if is_headless_file_mode else QWebEngineView()

class MockReviewer:
    """Enhanced MockReviewer that integrates with MockReviewerWindow."""
    _shortcutKeys = {}; _linkHandler = lambda self, url, _old: True
    def __init__(self):
        self.web = PureMockQWebEngineView() if is_headless_file_mode else QWebEngineView()
        self.reviewer_window = None
        self.card = None
    def show(self):
        logger.debug("MockReviewer: show() called.")
        if self.reviewer_window and hasattr(self.reviewer_window, 'show'): self.reviewer_window.show()
    def setCard(self, card): self.card = card; logger.debug(f"MockReviewer.setCard called with card: {card}")
    def showQuestion(self):
        logger.debug("MockReviewer: showQuestion() called.")
        if self.reviewer_window and hasattr(self.reviewer_window, 'load_current_card'): self.reviewer_window.load_current_card()
    def showAnswer(self):
        logger.debug("MockReviewer: showAnswer() called.")
        if self.reviewer_window and hasattr(self.reviewer_window, 'show_answer'): self.reviewer_window.show_answer()
    def answerCard(self, ease):
        logger.debug(f"MockReviewer: answerCard({ease}) called.")
        if self.reviewer_window and hasattr(self.reviewer_window, 'answer_card'): self.reviewer_window.answer_card(ease)

class MockAnkiWebView: """Mock for AnkiWebView."""
class MockWebContent: """Mock for WebContent."""
class MockSoundOrVideoTag: """Mock for SoundOrVideoTag."""
class MockAVPlayer: """Mock for AVPlayer."""

class MockAnkiUtils:
    """Mocks Anki's utils module."""
    def is_win(self): return sys.platform.startswith("win")
    def isWin(self): return self.is_win()

class MockAnkiBuildInfo:
    """Mocks Anki's buildinfo module."""
    def __init__(self): self.version = "2.1.66"

class MockProfileManager:
    """Mocks Anki's ProfileManager."""
    def __init__(self): self.name = "test_profile"

class MockThemeManager:
    """Mocks Anki's ThemeManager."""
    def __init__(self): self.night_mode = False

class MockDialogManager:
    """Mocks aqt.dialogs for handling dialog opening."""
    def __init__(self): self.dialogs = {}
    def open(self, name, parent, *args, **kwargs):
        logger.debug(f"aqt.dialogs.open called: {name}, parent: {parent}, args: {args}, kwargs: {kwargs}")
        return MockDialog(name)

class MockDialog:
    """Basic mock for dialogs."""
    def __init__(self, name): self.name = name; logger.debug(f"MockDialog created: {name}")
    def show(self): logger.debug(f"MockDialog.show called: {self.name}")
    def exec(self): logger.debug(f"MockDialog.exec called: {self.name}"); return 0

class MockMenuBar(QMenuBar):
    """Mocks a QMenuBar."""
    def __init__(self): super().__init__()
    def addMenu(self, menu): return super().addMenu(menu)

class MockForm:
    """Mocks the UI form setup."""
    def __init__(self):
        self.menubar = MockMenuBar()
        self.centralwidget = QWidget()
    def setupUi(self, main_window):
        if hasattr(main_window, 'setMenuBar'): main_window.setMenuBar(self.menubar)
        if hasattr(main_window, 'setCentralWidget'): main_window.setCentralWidget(self.centralwidget)

class MockMainWindow(QMainWindow):
    """Mocks Anki's main window (mw)."""
    def __init__(self):
        super().__init__()
        self.col = MockCollection()
        self.addonManager = MockAddonManager()
        self.pm = MockProfileManager()
        self.form = MockForm()
        self.form.setupUi(self)
        if hasattr(self, 'setGeometry'): self.setGeometry(100, 100, 800, 600)
        self.reviewer = MockReviewer()
        self.reviewer_window = MockReviewerWindow(self)
        self.reviewer.reviewer_window = self.reviewer_window

    def message_box(self, text):
        if hasattr(QMessageBox, 'setText'):
            msg = QMessageBox()
            msg.setText(text)
            msg.exec()
        else:
            logger.info(f"MockMessageBox: {text}")

class MockReviewerManager:
    """Mocks ReviewerManager for handling reviewer updates."""
    def __init__(self, settings_obj, main_pokemon, enemy_pokemon, ankimon_tracker):
        self.settings = settings_obj; self.main_pokemon = main_pokemon; self.enemy_pokemon = enemy_pokemon
        self.ankimon_tracker = ankimon_tracker; self.life_bar_injected = False; self.seconds = 0; self.myseconds = 0
        self.web = PureMockQWebEngineView() if is_headless_file_mode else QWebEngineView()

    def update_life_bar(self, reviewer, card, ease):
        js_code = "if(window.__ankimonHud) window.__ankimonHud.update('mock_html', 'mock_css');"
        if hasattr(reviewer.web.page(), 'eval'):
            reviewer.web.page().eval(js_code)
            logger.debug("MockReviewerManager.update_life_bar called and eval simulated.")
        else:
            logger.debug("MockReviewerManager.update_life_bar called, eval skipped (headless).")

class MockTestWindow(QWidget):
    """A mock window for testing Ankimon components."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'setWindowTitle'): self.setWindowTitle("Mock Ankimon Window")
        if hasattr(self, 'setGeometry'): self.setGeometry(300, 300, 800, 600)
        if hasattr(self, 'setLayout'):
            layout = QVBoxLayout(self); layout.addWidget(QLabel("This is a mock Ankimon window.")); self.setLayout(layout)
    def open_dynamic_window(self):
        logger.debug("MockTestWindow.open_dynamic_window called")
        if hasattr(self, 'show'): self.show()

class MockPokemonObject:
    """Mocks a Pokemon object."""
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("name", "MockPokemon"); self.id = kwargs.get("id", 1); self.level = kwargs.get("level", 1)
        self.ability = kwargs.get("ability", "mock_ability"); self.type = kwargs.get("type", ["Normal"]); self.stats = kwargs.get("stats", {})
        self.ev = kwargs.get("ev", {}); self.iv = kwargs.get("iv", {}); self.attacks = kwargs.get("attacks", [])
        self.base_experience = kwargs.get("base_experience", 0); self.growth_rate = kwargs.get("growth_rate", "medium")
        self.current_hp = kwargs.get("current_hp", 100); self.gender = kwargs.get("gender", "N"); self.shiny = kwargs.get("shiny", False)
        self.individual_id = kwargs.get("individual_id", "mock_id"); self.status = kwargs.get("status", None); self.volatile_status = kwargs.get("volatile_status", set())
        self.xp = kwargs.get("xp", 0); self.nickname = kwargs.get("nickname", ""); self.friendship = kwargs.get("friendship", 0)
        self.pokemon_defeated = kwargs.get("pokemon_defeated", 0); self.everstone = kwargs.get("everstone", False); self.mega = kwargs.get("mega", False)
        self.special_form = kwargs.get("special_form", None); self.evos = kwargs.get("evos", []); self.tier = kwargs.get("tier", None)
        self.captured_date = kwargs.get("captured_date", None); self.is_favorite = kwargs.get("is_favorite", False); self.held_item = kwargs.get("held_item", None)
    def to_dict(self): return {}
    @staticmethod
    def calc_stat(*args, **kwargs): return 100

class MockTrainerCard:
    """Mocks a Trainer Card."""
    def __init__(self, logger, main_pokemon, settings_obj, trainer_name, badge_count, trainer_id, level=1, xp=0, achievements=None, team="", image_path="", league="unranked"):
        self.logger = logger; self.main_pokemon = main_pokemon; self.settings_obj = settings_obj
        self.trainer_name = trainer_name; self.badge_count = badge_count; self.trainer_id = trainer_id
        self.level = level; self.xp = xp; self.achievements = achievements if achievements else []
        self.team = team; self.image_path = image_path; self.league = league
        self.cash = 0; self.favorite_pokemon = ""; self.highest_level = 0
    def get_highest_level_pokemon(self): return "None"
    def highest_pokemon_level(self): return 0
    def add_achievement(self, achievement): pass
    def set_team(self, team_pokemons): pass
    def display_card_data(self): return {}
    def xp_for_next_level(self): return 100
    def on_level_up(self): pass
    def gain_xp(self, tier, allow_to_choose_move=False): pass
    def check_level_up(self): pass

# --- Placeholder Mocks for Ankimon Components ---
# These are minimal mocks for components that might be imported by Ankimon's main logic.
# They are expanded upon in the `full_anki` section if needed.
class MockDataHandlerWindow:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): logger.debug("DataHandlerWindow.show_window called")

class MockSettingsWindow:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): logger.debug("SettingsWindow.show_window called")

class MockPokemonShopManager:
    def __init__(self, *args, **kwargs): pass
    def toggle_window(self): logger.debug("PokemonShopManager.toggle_window called")

class MockPokedex(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'setWindowTitle'): self.setWindowTitle("Mock Pokedex")
        if hasattr(self, 'setGeometry'): self.setGeometry(300, 300, 600, 400)
        if hasattr(self, 'setLayout'):
            layout = QVBoxLayout(self); layout.addWidget(QLabel("This is a mock Pokedex window.")); self.setLayout(layout)
    def show(self):
        logger.debug("MockPokedex.show called")
        if hasattr(self, 'exec'): self.exec()

class MockAchievementWindow:
    def __init__(self): pass
    def show_window(self): logger.debug("AchievementWindow.show_window called")

class MockAnkimonTrackerWindow:
    def __init__(self, *args, **kwargs): pass
    def toggle_window(self): logger.debug("AnkimonTrackerWindow.toggle_window called")

class MockLicense:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): logger.debug("License.show_window called")

class MockCredits:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): logger.debug("Credits.show_window called")

class MockTableWidget:
    def __init__(self, *args, **kwargs): pass
    def show_eff_chart(self): logger.debug("TableWidget.show_eff_chart called")

class MockIDTableWidget:
    def __init__(self, *args, **kwargs): pass
    def show_gen_chart(self): logger.debug("IDTableWidget.show_gen_chart called")

class MockVersionDialog:
    def __init__(self, *args, **kwargs): pass
    def open(self): logger.debug("VersionDialog.open called")

class MockDataHandler:
    def __init__(self, *args, **kwargs): pass

class MockEnemyPokemon:
    def __init__(self): self.type = ["Normal"]

class MockItemBagPath:
    def __init__(self): pass

class MockAchievements:
    def __init__(self): pass

class MockStarterWindow:
    def __init__(self): pass
    def display_fossil_pokemon(self, *args, **kwargs): logger.debug("StarterWindow.display_fossil_pokemon called")

class MockEvoWindow:
    def __init__(self): pass
    def display_pokemon_evo(self, *args, **kwargs): logger.debug("EvoWindow.display_pokemon_evo called")

class MockPokemonPC(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'setWindowTitle'): self.setWindowTitle("Mock Pokémon PC")
        if hasattr(self, 'setGeometry'): self.setGeometry(300, 300, 600, 400)
        if hasattr(self, 'setLayout'):
            layout = QVBoxLayout(self); layout.addWidget(QLabel("This is a mock Pokémon PC window.")); self.setLayout(layout)
    def show(self):
        logger.debug("MockPokemonPC.show called")
        if hasattr(self, 'exec'): self.exec()

# --- Mock Module Setup ---
# This section dynamically creates mock modules and injects them into sys.modules
# to simulate the Anki environment for Ankimon.

def setup_mock_modules(is_headless_mode):
    """Sets up mock Anki and aqt modules in sys.modules."""
    global mock_aqt_qt_module, mock_aqt_reviewer_module, mock_aqt_utils_module, \
           mock_aqt_gui_hooks_module, mock_aqt_webview_module, mock_aqt_sound_module, \
           mock_aqt_theme_module, mock_anki_hooks_module, mock_anki_collection_module, \
           mock_anki_utils_module, mock_anki_buildinfo_module, mock_aqt_dialogs_module, \
           mock_aqt_module, is_headless_file_mode, mw_instance

    is_headless_file_mode = is_headless_mode # Update global flag

    # --- Add Ankimon source to sys.path ---
    ankimon_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    if ankimon_src_path not in sys.path:
        sys.path.insert(0, ankimon_src_path)
        logger.debug(f"sys.path updated to include: {ankimon_src_path}")

    # --- Remove existing Anki/Aqt modules to ensure clean mocks ---
    modules_to_clear = [
        'aqt', 'anki', 'aqt.qt', 'aqt.reviewer', 'aqt.utils', 'aqt.gui_hooks',
        'aqt.webview', 'aqt.sound', 'aqt.theme', 'anki.hooks', 'anki.collection',
        'anki.utils', 'anki.buildinfo', 'aqt.dialogs'
    ]
    for module_name in modules_to_clear:
        if module_name in sys.modules:
            del sys.modules[module_name]
            logger.debug(f"Removed existing module from sys.modules: {module_name}")

    # --- Create and inject mock modules ---

    # aqt.qt
    mock_aqt_qt_module = ModuleType('aqt.qt')
    mock_aqt_qt_module.QDialog = QDialog
    mock_aqt_qt_module.qconnect = MockUtils().qconnect
    mock_aqt_qt_module.QWidget = QWidget
    mock_aqt_qt_module.QVBoxLayout = QVBoxLayout
    mock_aqt_qt_module.QHBoxLayout = QHBoxLayout
    mock_aqt_qt_module.QLabel = QLabel
    mock_aqt_qt_module.QPushButton = QPushButton
    mock_aqt_qt_module.QLineEdit = QLineEdit
    mock_aqt_qt_module.QSizePolicy = QSizePolicy
    mock_aqt_qt_module.QFont = QFont
    mock_aqt_qt_module.QPixmap = QPixmap
    mock_aqt_qt_module.QImage = QImage
    mock_aqt_qt_module.QPainter = QPainter
    mock_aqt_qt_module.QGridLayout = QGridLayout
    mock_aqt_qt_module.QFrame = QFrame
    mock_aqt_qt_module.QMessageBox = QMessageBox
    mock_aqt_qt_module.QFontDatabase = QFontDatabase
    mock_aqt_qt_module.QToolTip = QToolTip
    mock_aqt_qt_module.QFile = QFile
    mock_aqt_qt_module.QUrl = QUrl
    mock_aqt_qt_module.Qt = Qt
    mock_aqt_qt_module.QSize = QSize
    mock_aqt_qt_module.QCheckBox = QCheckBox
    sys.modules['aqt.qt'] = mock_aqt_qt_module
    logger.debug("Mocked 'aqt.qt' module.")

    # aqt.reviewer
    mock_aqt_reviewer_module = ModuleType('aqt.reviewer')
    mock_aqt_reviewer_module.Reviewer = MockReviewer
    sys.modules['aqt.reviewer'] = mock_aqt_reviewer_module
    logger.debug("Mocked 'aqt.reviewer' module.")

    # aqt.utils
    mock_aqt_utils_module = ModuleType('aqt.utils')
    mock_aqt_utils_instance = MockUtils()
    mock_aqt_utils_module.downArrow = mock_aqt_utils_instance.downArrow
    mock_aqt_utils_module.showWarning = mock_aqt_utils_instance.showWarning
    mock_aqt_utils_module.showInfo = mock_aqt_utils_instance.showInfo
    mock_aqt_utils_module.tr = mock_aqt_utils_instance.tr
    mock_aqt_utils_module.tooltip = mock_aqt_utils_instance.tooltip
    mock_aqt_utils_module.qconnect = mock_aqt_utils_instance.qconnect
    mock_aqt_utils_module.QWebEngineSettings = MockQWebEngineSettings
    mock_aqt_utils_module.QWebEnginePage = PureMockQWebEnginePage if is_headless_mode else MockQWebEnginePage
    mock_aqt_utils_module.QWebEngineView = PureMockQWebEngineView if is_headless_mode else QWebEngineView
    sys.modules['aqt.utils'] = mock_aqt_utils_module
    logger.debug("Mocked 'aqt.utils' module.")

    # aqt.gui_hooks
    mock_aqt_gui_hooks_module = ModuleType('aqt.gui_hooks')
    mock_aqt_gui_hooks_instance = MockGuiHooks()
    mock_aqt_gui_hooks_module.addHook = mock_aqt_gui_hooks_instance.addHook
    mock_aqt_gui_hooks_module.webview_will_set_content = mock_aqt_gui_hooks_instance.webview_will_set_content
    mock_aqt_gui_hooks_module.reviewer_will_end = mock_aqt_gui_hooks_instance.reviewer_will_end
    mock_aqt_gui_hooks_module.reviewer_did_answer_card = mock_aqt_gui_hooks_instance.reviewer_did_answer_card
    mock_aqt_gui_hooks_module.theme_did_change = mock_aqt_gui_hooks_instance.theme_did_change
    mock_aqt_gui_hooks_module.reviewer_did_show_question = mock_aqt_gui_hooks_instance.reviewer_did_show_question
    mock_aqt_gui_hooks_module.reviewer_did_show_answer = mock_aqt_gui_hooks_instance.reviewer_did_show_answer
    mock_aqt_gui_hooks_module.addon_config_editor_will_display_json = mock_aqt_gui_hooks_instance.addon_config_editor_will_display_json
    mock_aqt_gui_hooks_module.reviewer_will_answer_card = mock_aqt_gui_hooks_instance.reviewer_will_answer_card
    mock_aqt_gui_hooks_module.profile_did_open = mock_aqt_gui_hooks_instance.profile_did_open
    sys.modules['aqt.gui_hooks'] = mock_aqt_gui_hooks_module
    logger.debug("Mocked 'aqt.gui_hooks' module.")

    # aqt.webview
    mock_aqt_webview_module = ModuleType('aqt.webview')
    mock_aqt_webview_module.WebContent = MockWebContent
    mock_aqt_webview_module.AnkiWebView = PureMockQWebEngineView if is_headless_mode else QWebEngineView
    sys.modules['aqt.webview'] = mock_aqt_webview_module
    logger.debug("Mocked 'aqt.webview' module.")

    # aqt.sound
    mock_aqt_sound_module = ModuleType('aqt.sound')
    mock_aqt_sound_module.SoundOrVideoTag = MockSoundOrVideoTag
    mock_aqt_sound_module.AVPlayer = MockAVPlayer
    sys.modules['aqt.sound'] = mock_aqt_sound_module
    logger.debug("Mocked 'aqt.sound' module.")

    # aqt.theme
    mock_aqt_theme_module = ModuleType('aqt.theme')
    mock_aqt_theme_module.theme_manager = MockThemeManager()
    sys.modules['aqt.theme'] = mock_aqt_theme_module
    logger.debug("Mocked 'aqt.theme' module.")

    # anki.hooks
    mock_anki_hooks_module = ModuleType('anki.hooks')
    mock_anki_hooks_instance = MockAnkiHooks()
    mock_anki_hooks_module.addHook = mock_anki_hooks_instance.addHook
    mock_anki_hooks_module.wrap = mock_anki_hooks_instance.wrap
    sys.modules['anki.hooks'] = mock_anki_hooks_module
    logger.debug("Mocked 'anki.hooks' module.")

    # anki.collection
    mock_anki_collection_module = ModuleType('anki.collection')
    mock_anki_collection_module.Collection = MockCollection
    sys.modules['anki.collection'] = mock_anki_collection_module
    logger.debug("Mocked 'anki.collection' module.")

    # anki.utils
    mock_anki_utils_module = ModuleType('anki.utils')
    mock_anki_utils_instance = MockAnkiUtils()
    mock_anki_utils_module.is_win = mock_anki_utils_instance.is_win
    mock_anki_utils_module.isWin = mock_anki_utils_instance.isWin
    sys.modules['anki.utils'] = mock_anki_utils_module
    logger.debug("Mocked 'anki.utils' module.")

    # anki.buildinfo
    mock_anki_buildinfo_module = ModuleType('anki.buildinfo')
    mock_anki_buildinfo_instance = MockAnkiBuildInfo()
    mock_anki_buildinfo_module.version = mock_anki_buildinfo_instance.version
    sys.modules['anki.buildinfo'] = mock_anki_buildinfo_module
    logger.debug("Mocked 'anki.buildinfo' module.")

    # Top-level anki module
    mock_anki_module = ModuleType('anki')
    mock_anki_module.__path__ = []
    mock_anki_module.hooks = mock_anki_hooks_module
    mock_anki_module.collection = mock_anki_collection_module
    mock_anki_module.utils = mock_anki_utils_module
    mock_anki_module.buildinfo = mock_anki_buildinfo_module
    sys.modules['anki'] = mock_anki_module
    logger.debug("Mocked top-level 'anki' module.")

    # aqt.dialogs
    dialogs_manager = MockDialogManager()
    mock_aqt_dialogs_module = ModuleType('aqt.dialogs')
    mock_aqt_dialogs_module.open = dialogs_manager.open
    sys.modules['aqt.dialogs'] = mock_aqt_dialogs_module
    logger.debug("Mocked 'aqt.dialogs' module.")

    # Top-level aqt module
    mock_aqt_module = ModuleType('aqt')
    mock_aqt_module.__path__ = []
    # Instantiate MockMainWindow and assign it to mw_instance here
    mw_instance = MockMainWindow()
    mock_aqt_module.mw = mw_instance
    mock_aqt_module.gui_hooks = mock_aqt_gui_hooks_module
    mock_aqt_module.utils = mock_aqt_utils_module
    mock_aqt_module.qt = mock_aqt_qt_module
    mock_aqt_module.reviewer = mock_aqt_reviewer_module
    mock_aqt_module.webview = mock_aqt_webview_module
    mock_aqt_module.sound = mock_aqt_sound_module
    mock_aqt_module.theme = mock_aqt_theme_module
    mock_aqt_module.dialogs = mock_aqt_dialogs_module
    mock_aqt_module.qconnect = MockUtils().qconnect
    mock_aqt_module.QDialog = QDialog
    mock_aqt_module.QVBoxLayout = QVBoxLayout
    mock_aqt_module.QWebEngineView = QWebEngineView
    sys.modules['aqt'] = mock_aqt_module
    logger.debug("Mocked top-level 'aqt' module.")

    logger.info("Anki/aqt mock environment set up successfully.")
    return mock_aqt_gui_hooks_module # Return hooks for potential use in self-tests

# --- Self-Test Harness ---
def run_self_tests(app_instance, is_headless_test):
    """
    Runs self-tests to verify the test environment setup.
    Returns True if all tests pass, False otherwise.
    """
    logger.info("--- Running Self-Tests for Ankimon Test Environment ---")
    all_tests_passed = True

    # Use a temporary logger for self-test specific output
    test_logger = logging.getLogger('SelfTestLogger')
    log_capture_string = io.StringIO()
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.ERROR) # Capture only errors from self-tests
    test_logger.addHandler(ch)
    test_logger.propagate = False

    # Test 1: sys.path setup
    expected_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    if expected_path in sys.path:
        logger.info("[PASS] sys.path contains Ankimon source directory.")
    else:
        test_logger.error("[FAIL] sys.path does not contain Ankimon source directory.")
        all_tests_passed = False

    # Test 2: QApplication presence
    if not is_headless_test:
        if app_instance and isinstance(app_instance, QApplication):
            logger.info("[PASS] QApplication instance is present.")
        else:
            test_logger.error("[FAIL] QApplication instance is NOT present.")
            all_tests_passed = False
    else:
        if isinstance(app_instance, DummyQApplication):
            logger.info("[PASS] DummyQApplication instance is present in headless mode.")
        else:
            test_logger.error("[FAIL] DummyQApplication instance is NOT present in headless mode.")
            all_tests_passed = False

    # Test 3: Mocks presence and key attributes
    expected_mocks = {
        'aqt.qt': ['QDialog', 'QWidget', 'QApplication'],
        'aqt.reviewer': ['Reviewer'],
        'aqt.utils': ['showWarning', 'showInfo', 'QWebEngineView'],
        'aqt.gui_hooks': ['reviewer_did_show_question', 'reviewer_did_answer_card'],
        'aqt.webview': ['WebContent', 'AnkiWebView'],
        'anki.hooks': ['addHook', 'wrap'],
        'anki.collection': ['Collection'],
        'anki.utils': ['is_win', 'isWin'],
        'anki.buildinfo': ['version'],
        'aqt.dialogs': ['open'],
        'aqt': ['mw', 'gui_hooks', 'utils', 'qt', 'reviewer', 'webview', 'sound', 'theme', 'dialogs']
    }
    for module_name, attributes in expected_mocks.items():
        if module_name in sys.modules:
            logger.info(f"[PASS] Mock module '{module_name}' is present.")
            mock_module = sys.modules[module_name]
            for attr in attributes:
                if hasattr(mock_module, attr):
                    logger.debug(f"  [PASS] Attribute '{attr}' found in '{module_name}'.")
                else:
                    test_logger.error(f"  [FAIL] Attribute '{attr}' not found in '{module_name}'.")
                    all_tests_passed = False
        else:
            test_logger.error(f"[FAIL] Mock module '{module_name}' is NOT present.")
            all_tests_passed = False

    # Test 4: Error handling for missing/corrupt configs
    temp_dir = Path(tempfile.gettempdir())

    # Test missing JSON file
    temp_missing_file = temp_dir / "non_existent_file_for_test.json"
    try:
        load_ankimon_json(temp_missing_file)
        test_logger.error(f"[FAIL] load_ankimon_json did NOT raise ConfigError for missing file: {temp_missing_file}")
        all_tests_passed = False
    except ConfigError as e:
        if f"Required JSON file not found: {temp_missing_file}" in str(e):
            logger.info("[PASS] load_ankimon_json raises ConfigError for missing file.")
        else:
            test_logger.error(f"[FAIL] load_ankimon_json raised wrong ConfigError for missing file: {e}")
            all_tests_passed = False
    except Exception as e:
        test_logger.error(f"[FAIL] load_ankimon_json raised unexpected error for missing file: {type(e).__name__} - {e}")
        all_tests_passed = False

    # Test corrupt JSON file
    temp_corrupt_file = temp_dir / "corrupt_config_for_test.json"
    with open(temp_corrupt_file, "w") as f: f.write("{invalid json")
    try:
        load_ankimon_json(temp_corrupt_file)
        test_logger.error(f"[FAIL] load_ankimon_json did NOT raise ConfigError for corrupt JSON: {temp_corrupt_file}")
        all_tests_passed = False
    except ConfigError as e:
        if f"Corrupt JSON in file: {temp_corrupt_file}" in str(e):
            logger.info("[PASS] load_ankimon_json raises ConfigError for corrupt JSON.")
        else:
            test_logger.error(f"[FAIL] load_ankimon_json raised wrong ConfigError for corrupt JSON: {e}")
            all_tests_passed = False
    except Exception as e:
        test_logger.error(f"[FAIL] load_ankimon_json raised unexpected error for corrupt JSON: {type(e).__name__} - {e}")
        all_tests_passed = False
    finally:
        if temp_corrupt_file.exists(): temp_corrupt_file.unlink()

    # Clean up temporary logger
    test_logger.removeHandler(ch)

    if all_tests_passed:
        logger.info("--- All self-tests PASSED! ---")
        return True
    else:
        logger.error("--- Some self-tests FAILED! ---")
        # Print captured error logs
        if log_capture_string.getvalue():
            logger.error("\n--- Captured Error Logs During Self-Tests ---")
            for line in log_capture_string.getvalue().splitlines():
                logger.error(line)
            logger.error("---------------------------------------------\n")
        return False

# --- Main Execution Logic ---

# Run self-tests if requested
if args.selftest:
    # Determine headless mode for self-tests based on environment variable or default
    is_headless_selftest = os.environ.get('ANKIMON_HEADLESS_SELFTEST', 'False') == 'True'
    setup_mock_modules(is_headless_selftest) # Setup mocks for self-test validation
    if run_self_tests(app, is_headless_selftest):
        logger.info("Self-tests completed successfully. Exiting.")
        sys.exit(0)
    else:
        logger.error("Self-tests failed. Exiting with error.")
        sys.exit(1)

# Setup the test environment for actual execution (file or full-anki)
# Use is_headless_file_mode determined earlier
mock_aqt_gui_hooks_module = setup_mock_modules(is_headless_file_mode)

# --- Execute based on command-line arguments ---
if args.file:
    # Test an individual file
    file_path = os.path.abspath(args.file)
    if not os.path.exists(file_path):
        logger.error(f"Error: File not found at {file_path}")
        sys.exit(1)

    try:
        spec = importlib.util.spec_from_file_location("test_module", file_path)
        test_module = importlib.util.module_from_spec(spec)
        sys.modules["test_module"] = test_module
        spec.loader.exec_module(test_module)
        logger.info(f"Successfully executed test file: {file_path}")

        # Attempt to display any QWidget or QDialog found in the test module
        displayed_widget = None
        for name in dir(test_module):
            obj = getattr(test_module, name)
            if isinstance(obj, (QWidget, QDialog)):
                if hasattr(obj, 'show'):
                    obj.show()
                    displayed_widget = obj
                    break
        if not displayed_widget:
            logger.info(f"No QWidget or QDialog found to display in {file_path}")

        # Process events if QApplication is available
        if app and hasattr(app, 'processEvents'):
            app.processEvents()

    except Exception as e:
        logger.error(f"Error executing test file {file_path}: {type(e).__name__}: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Ensure application quits if it was started for GUI mode
        if app and hasattr(app, 'quit'):
            app.quit()
        sys.exit(0)

elif args.full_anki:
    if not app or not isinstance(app, QApplication):
        logger.error("Cannot run full Anki-like interface without a graphical environment (PyQt6 QApplication).")
        sys.exit(1)

    # --- Full Anki-like Interface Setup ---
    logger.info("Starting enhanced Ankimon test environment (Full Anki Mode)...")

    # Import Ankimon components, using mocks as fallbacks
    _Settings = MockSettings
    _Translator = MockTranslator
    _ShowInfoLogger = MockShowInfoLogger
    _PokemonCollectionDialog = MockDialog
    _ItemWindow = MockDialog
    _PokemonPC = MockDialog
    _AnkimonTrackerWindow = MockAnkimonTrackerWindow

    try:
        from Ankimon.menu_buttons import create_menu_actions, initialize_ankimon_menu
        from Ankimon.pyobj.settings import Settings as _Settings
        from Ankimon.pyobj.translator import Translator as _Translator
        from Ankimon.pyobj.InfoLogger import ShowInfoLogger as _ShowInfoLogger
        from Ankimon.pyobj.collection_dialog import PokemonCollectionDialog as _PokemonCollectionDialog
        from Ankimon.pyobj.item_window import ItemWindow as _ItemWindow
        from Ankimon.pyobj.pc_box import PokemonPC as _PokemonPC
        from Ankimon.gui_entities import AnkimonTrackerWindow as _AnkimonTrackerWindow
        logger.info("Ankimon components imported successfully.")
    except ImportError as e:
        logger.warning(f"Could not import some Ankimon components: {e}. Using fallback mocks.")
    except Exception as e:
        logger.warning(f"An unexpected error occurred during Ankimon component import: {e}. Using fallback mocks.")

    # Instantiate core objects
    settings_obj = _Settings()
    translator_obj = _Translator(language=int(settings_obj.get("misc.language", 9)))
    logger_obj = _ShowInfoLogger()

    # Initialize Ankimon menu structure
    pokemenu, game_menu, profile_menu, collection_menu, export_menu, help_menu, debug_menu = initialize_ankimon_menu()

    # Instantiate Ankimon-specific objects for menu actions and reviewer
    main_pokemon_obj = MockPokemonObject()
    enemy_pokemon_obj = MockEnemyPokemon()
    achievements_obj = MockAchievements()
    starter_window_obj = MockStarterWindow()
    evo_window_obj = MockEvoWindow()
    ankimon_tracker_obj = _AnkimonTrackerWindow(mw_instance) # Use resolved class
    reviewer_obj = MockReviewerManager(settings_obj, main_pokemon_obj, enemy_pokemon_obj, ankimon_tracker_obj)

    # Create dummy itembag.json for potential use by ItemWindow
    temp_dir = Path(tempfile.gettempdir())
    itembag_path = temp_dir / "itembag.json"
    with open(itembag_path, "w") as f: json.dump([], f)

    # Create dialog objects using resolved (real or mock) classes
    try:
        collection_dialog_obj = _PokemonCollectionDialog(
            logger=logger_obj, translator=translator_obj, reviewer_obj=reviewer_obj,
            test_window=MockTestWindow(), settings_obj=settings_obj,
            main_pokemon=main_pokemon_obj, parent=mw_instance
        )
        item_window_obj = _ItemWindow(
            logger=logger_obj, main_pokemon=main_pokemon_obj, enemy_pokemon=enemy_pokemon_obj,
            itembagpath=str(itembag_path), achievements=achievements_obj,
            starter_window=starter_window_obj, evo_window=evo_window_obj
        )
        pokemon_pc_obj = _PokemonPC(
            logger=logger_obj, translator=translator_obj, reviewer_obj=reviewer_obj,
            test_window=MockTestWindow(), settings=settings_obj,
            main_pokemon=main_pokemon_obj, parent=mw_instance
        )
        logger.info("Ankimon dialog objects created successfully.")
    except Exception as e:
        logger.warning(f"Could not create some dialog objects: {e}. Falling back to basic mocks.")
        collection_dialog_obj = MockDialog("PokemonCollection")
        item_window_obj = MockDialog("ItemWindow")
        pokemon_pc_obj = MockDialog("PokemonPC")

    # Create other necessary mock objects
    achievement_window_obj = MockAchievementWindow()
    trainer_card_obj = MockTrainerCard(
        logger=logger_obj, main_pokemon=main_pokemon_obj, settings_obj=settings_obj,
        trainer_name="MockTrainer", badge_count=0, trainer_id=123,
    )
    data_handler_window_obj = MockDataHandlerWindow(mw_instance)
    settings_window_obj = MockSettingsWindow(mw_instance)
    shop_manager_obj = MockPokemonShopManager(mw_instance)
    pokedex_window_obj = MockPokedex(mw_instance)
    eff_chart_obj = MockTableWidget(mw_instance)
    gen_id_chart_obj = MockIDTableWidget(mw_instance)
    credits_obj = MockCredits(mw_instance)
    license_obj = MockLicense(mw_instance)
    version_dialog_obj = MockVersionDialog(mw_instance)
    data_handler_obj = MockDataHandler()

    # Define mock functions for menu actions
    def mock_open_team_builder(): logger.debug("Mock open_team_builder called")
    def mock_export_to_pkmn_showdown(): logger.debug("Mock export_to_pkmn_showdown called")
    def mock_export_all_pkmn_showdown(): logger.debug("Mock export_all_pkmn_showdown called")
    def mock_flex_pokemon_collection(): logger.debug("Mock flex_pokemon_collection called")
    def mock_open_help_window(online_connectivity): logger.debug(f"Mock open_help_window called with {online_connectivity}")
    def mock_report_bug(): logger.debug("Mock report_bug called")
    def mock_rate_addon_url(): logger.debug("Mock rate_addon_url called")
    def mock_join_discord_url(): logger.debug("Mock join_discord_url called")
    def mock_open_leaderboard_url(): logger.debug("Mock open_leaderboard_url called")

    # Call create_menu_actions to populate the Ankimon menu
    try:
        create_menu_actions(
            database_complete=True, online_connectivity=True,
            pokecollection_win=collection_dialog_obj, item_window=item_window_obj,
            test_window=MockTestWindow(), achievement_bag=achievement_window_obj,
            open_team_builder=mock_open_team_builder,
            export_to_pkmn_showdown=mock_export_to_pkmn_showdown,
            export_all_pkmn_showdown=mock_export_all_pkmn_showdown,
            flex_pokemon_collection=mock_flex_pokemon_collection,
            eff_chart=eff_chart_obj, gen_id_chart=gen_id_chart_obj,
            credits=credits_obj, license=license_obj,
            open_help_window=mock_open_help_window, report_bug=mock_report_bug,
            rate_addon_url=mock_rate_addon_url, version_dialog=version_dialog_obj,
            trainer_card=trainer_card_obj, ankimon_tracker_window=ankimon_tracker_obj,
            logger=logger_obj, data_handler_window=data_handler_window_obj,
            settings_window=settings_window_obj, shop_manager=shop_manager_obj,
            pokedex_window=pokedex_window_obj, ankimon_key="Ctrl+N",
            join_discord_url=mock_join_discord_url, open_leaderboard_url=mock_open_leaderboard_url,
            settings_obj=settings_obj,
            addon_dir=Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'Ankimon'))),
            data_handler_obj=data_handler_obj, pokemon_pc=pokemon_pc_obj,
            pokemenu=pokemenu, game_menu=game_menu, profile_menu=profile_menu,
            collection_menu=collection_menu, export_menu=export_menu,
            help_menu=help_menu, debug_menu=debug_menu,
        )
        logger.info("Ankimon menu actions created successfully.")
    except Exception as e:
        logger.warning(f"Could not create menu actions: {e}")

    # Add custom actions to the menu for testing
    if hasattr(mw_instance.pokemenu, 'addSeparator'): mw_instance.pokemenu.addSeparator()

    # Enhanced Mock Reviewer action
    if hasattr(QAction, '__init__'):
        enhanced_reviewer_action = QAction("🎮 Open Enhanced Mock Reviewer", mw_instance)
        enhanced_reviewer_action.triggered.connect(lambda: mw_instance.reviewer_window.show())
        if hasattr(mw_instance.pokemenu, 'addAction'): mw_instance.pokemenu.addAction(enhanced_reviewer_action)

    # Test Hooks action
    if hasattr(QAction, '__init__'):
        test_hooks_action = QAction("🔧 Test Ankimon Hooks", mw_instance)
        def test_hooks():
            logger.debug("Testing Ankimon hooks...")
            test_card = MockCard(999, "Test Question", "Test Answer")
            if mock_aqt_gui_hooks_module:
                for func in mock_aqt_gui_hooks_module.reviewer_did_show_question: func(test_card)
                for func in mock_aqt_gui_hooks_module.reviewer_did_answer_card: func(None, test_card, 3)
            logger.debug("Hook testing completed")
        test_hooks_action.triggered.connect(test_hooks)
        if hasattr(mw_instance.pokemenu, 'addAction'): mw_instance.pokemenu.addAction(test_hooks_action)

    # Debug Info action
    if hasattr(QAction, '__init__'):
        debug_info_action = QAction("ℹ️ Show Debug Info", mw_instance)
        def show_debug_info():
            num_mocked_modules = len([m for m in sys.modules.keys() if m.startswith(('aqt', 'anki'))])
            num_q_hooks = len(mock_aqt_gui_hooks_module.reviewer_did_show_question) if mock_aqt_gui_hooks_module else 0
            num_a_hooks = len(mock_aqt_gui_hooks_module.reviewer_did_show_answer) if mock_aqt_gui_hooks_module else 0
            num_ans_hooks = len(mock_aqt_gui_hooks_module.reviewer_did_answer_card) if mock_aqt_gui_hooks_module else 0
            reviewer_status = 'Active' if hasattr(mw_instance, 'reviewer_window') else 'Inactive'
            cards_available = len(mw_instance.reviewer_window.cards) if hasattr(mw_instance, 'reviewer_window') and hasattr(mw_instance.reviewer_window, 'cards') else 'N/A'
            info = f"Enhanced Ankimon Test Environment Debug Info:\n\nMocked Modules: {num_mocked_modules}\nActive Hooks:\n- reviewer_did_show_question: {num_q_hooks}\n- reviewer_did_show_answer: {num_a_hooks}\n- reviewer_did_answer_card: {num_ans_hooks}\n\nReviewer Status: {reviewer_status}\nCards Available: {cards_available}"
            mw_instance.message_box(info)
        debug_info_action.triggered.connect(show_debug_info)
        if hasattr(mw_instance.pokemenu, 'addAction'): mw_instance.pokemenu.addAction(debug_info_action)

    logger.info("Enhanced test environment setup complete!")
    logger.info("Available actions: Enhanced Mock Reviewer, Test Ankimon Hooks, Show Debug Info, and Ankimon menu items.")

    # Show the mock main window and start the Qt event loop
    if hasattr(mw_instance, 'show'): mw_instance.show()
    if hasattr(app, 'exec'): sys.exit(app.exec())
    else:
        logger.warning("Cannot start Qt event loop in headless mode.")
        sys.exit(0)

else:
    # Display usage information if no specific mode is selected
    logger.info("Enhanced Ankimon Test Environment")
    logger.info("Usage:")
    logger.info("  python run_test_env.py --file <path>     Test an individual Python file")
    logger.info("  python run_test_env.py --full-anki       Run full Anki-like interface with enhanced features")
    logger.info("  python run_test_env.py --selftest        Run self-tests and exit")
    logger.info("  --debug / --log-level <level>            Control logging verbosity")
    sys.exit(1)
