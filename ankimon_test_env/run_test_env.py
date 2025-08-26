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

# Configure logging
# To enable debug logging, run with --log-level DEBUG or --debug
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class ConfigError(Exception):
    """Custom exception for errors related to Ankimon configuration loading."""
    pass

# Parse command-line arguments early to configure logging and QApplication
parser = argparse.ArgumentParser(description="Enhanced Ankimon Test Environment")
parser.add_argument('--file', type=str, help='Path to an individual Python file to test')
parser.add_argument('--full-anki', action='store_true', help='Run a full Anki-like interface with enhanced Ankimon menu and reviewer')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
parser.add_argument('--selftest', action='store_true', help='Run self-tests and exit')
parser.add_argument('--log-level', type=str, default='INFO', help='Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)')
args = parser.parse_args()

# Set logging level based on argument
if args.debug:
    numeric_level = logging.DEBUG
else:
    numeric_level = getattr(logging, args.log_level.upper(), None)

if not isinstance(numeric_level, int):
    raise ValueError('Invalid log level: %s' % args.log_level)
logging.getLogger().setLevel(numeric_level)

# Initialize QApplication if a GUI is required. This must happen only once.
app = None
if not args.selftest or (args.selftest and not os.environ.get('ANKIMON_HEADLESS_SELFTEST', 'False') == 'True'):
    # Only create QApplication if not running headless selftest
    try:
        from PyQt6.QtWidgets import QApplication
        # Check if QApplication already exists
        if QApplication.instance():
            app = QApplication.instance()
            logging.debug("QApplication instance already exists, reusing.")
        else:
            app = QApplication(sys.argv)
            logging.debug("New QApplication instance created.")
    except ImportError as e:
        logging.warning(f"PyQt6 not installed or available: {e}. Running in headless mode.")
        if args.full_anki and not args.selftest:
            logging.critical("Full Anki-like interface requires PyQt6 but it's not available. Exiting.")
            sys.exit(1)
else:
    logging.debug("Running in headless mode, skipping QApplication instantiation.")

# Determine if we are in headless file mode (no GUI for the webview)
is_headless_file_mode = bool(args.file) or os.environ.get('ANKIMON_HEADLESS_SELFTEST', 'False') == 'True'


# Import PyQt6 components if a GUI is required. QtWebEngineWidgets must be imported early.
if not is_headless_file_mode: # If not in headless mode, we expect a GUI and try to import Qt
    try:
        from PyQt6.QtWidgets import QMainWindow, QMessageBox, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSizePolicy, QGridLayout, QFrame, QToolTip, QMenuBar, QMenu, QCheckBox
        from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter, QFontDatabase, QAction
        from PyQt6.QtCore import Qt, QSize, QFile, QUrl, QTimer
        # Crucial: Import QWebEngineView here, before QApplication is instantiated if possible
        from PyQt6.QtWebEngineWidgets import QWebEngineView
    except ImportError as e:
        logging.warning(f"PyQt6 or QtWebEngineWidgets not fully available: {e}. Running in headless mode for GUI components.")
        # Fallback to dummy classes if import fails
        is_headless_file_mode = True # Force headless mode for all subsequent checks
        
# Define dummy PyQt6 components for headless mode or if imports failed
if is_headless_file_mode:
    logging.debug("Defining dummy PyQt6 components for headless operation.")
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
    class QLabel:
        def __init__(self, text=""): self.text = text
    class QPushButton:
        def __init__(self, text=""): self.text = text
        def setMinimumHeight(self, height): pass
        def clicked(self):
            class Signal:
                def connect(self, func): self.func = func
            return Signal()
        def hide(self): pass
        def show(self): pass
    class QLineEdit: pass
    class QSizePolicy: pass
    class QGridLayout: pass
    class QFrame: pass
    class QToolTip: pass
    class QMenuBar: pass
    class QMenu: pass
    class QCheckBox: pass
    class QFont: pass
    class QPixmap: pass
    class QImage: pass
    class QPainter: pass
    class QFontDatabase: pass
    class QAction:
        def __init__(self, text, parent=None): pass
        def triggered(self):
            class Signal:
                def connect(self, func): self.func = func
            return Signal()
    class Qt:
        class SizeHint: pass
        AlignLeft = 0
        AlignRight = 0
        AlignCenter = 0
        AlignTop = 0
        AlignBottom = 0
        TextWordWrap = 0
    class QSize: pass
    class QFile: pass
    class QUrl: pass
    class QTimer:
        @staticmethod
        def singleShot(ms, func): pass
    class QWebEngineView(QWidget): # Inherit from QWidget or a dummy QWidget
        def __init__(self):
            super().__init__()
            self._page = PureMockQWebEnginePage()
        def page(self): return self._page
        def setHtml(self, html_content): logging.debug(f"DummyQWebEngineView.setHtml: {html_content[:100]}...")
        def setMinimumHeight(self, height): pass

# Re-evaluate app creation after ensuring QWebEngineView is imported or mocked
if not args.selftest or (args.selftest and not os.environ.get('ANKIMON_HEADLESS_SELFTEST', 'False') == 'True'):
    # Only create QApplication if not running headless selftest
    try:
        from PyQt6.QtWidgets import QApplication
        if QApplication.instance():
            app = QApplication.instance()
            logging.debug("QApplication instance already exists, reusing.")
        else:
            app = QApplication(sys.argv)
            logging.debug("New QApplication instance created.")
    except ImportError as e:
        logging.warning(f"PyQt6 not available for QApplication: {e}. Running in headless mode.")
        if args.full_anki and not args.selftest:
            logging.critical("Full Anki-like interface requires PyQt6 QApplication but it's not available. Exiting.")
            sys.exit(1)
else:
    logging.debug("Running in headless mode, skipping QApplication instantiation.")
    class DummyQApplication: # Define DummyQApplication here to ensure it's always available
        def instance(self): return None
        def processEvents(self): pass
        def quit(self): pass
        def exec(self): return 0
    app = DummyQApplication() # Assign dummy app for consistent API

# Helper to load JSON data from Ankimon's user_files
def load_ankimon_json(file_name: Path):
    base_path = Path(__file__).parent.parent / "src" / "Ankimon" / "user_files"
    file_path = base_path / file_name
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"ConfigError: JSON file not found: {file_path}")
        raise ConfigError(f"Required JSON file not found: {file_path}")
    except json.JSONDecodeError:
        logging.error(f"ConfigError: Error decoding JSON from file: {file_path}")
        raise ConfigError(f"Corrupt JSON in file: {file_path}")

# Helper to load Ankimon's config.json
def load_ankimon_config():
    config_path = Path(__file__).parent.parent / "src" / "Ankimon" / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.error(f"ConfigError: Ankimon config.json not found: {config_path}")
        raise ConfigError(f"Ankimon config.json not found: {config_path}")
    except json.JSONDecodeError:
        logging.error(f"ConfigError: Error decoding JSON from Ankimon config.json: {config_path}")
        raise ConfigError(f"Corrupt JSON in Ankimon config.json: {config_path}")

class MockAddonManager:
    """Mocks Anki's addonManager object, providing methods for config management.
    This mock allows Ankimon to load and save its configuration within the test environment.
    It simulates the behavior of Anki's addon manager for `getConfig` and `writeConfig`.
    """
    def __init__(self):
        # Use a dictionary to store configurations for different addons
        self._configs = {}
        # Load Ankimon's default config and store it under its ID
        try:
            ankimon_default_config = load_ankimon_config()
            self._configs["Ankimon.config_var"] = ankimon_default_config
        except ConfigError as e:
            logging.warning(f"MockAddonManager could not load Ankimon config: {e}. Using empty config.")
            self._configs["Ankimon.config_var"] = {}
        logging.debug(f"MockAddonManager.__init__: Initialized _configs: {self._configs}")
        self.addonsFolder = Path(__file__).parent.parent / "src" / "Ankimon" # Mock addonsFolder

    def getConfig(self, name):
        logging.debug(f"MockAddonManager.getConfig: Called for {name}. Current _configs: {self._configs}")
        # Return the config for the specific addon, or an empty dict if not found
        return self._configs.get(name, {})

    def writeConfig(self, name, config):
        logging.debug(f"MockAddonManager.writeConfig: Called for {name} with {config}. Before update _configs: {self._configs}")
        # Update the config for the specific addon. Merge if existing.
        current_config = self._configs.get(name, {})
        current_config.update(config)
        self._configs[name] = current_config
        logging.debug(f"MockAddonManager.writeConfig: After update _configs: {self._configs}")

    def setWebExports(self, name, pattern):
        logging.debug(f"setWebExports called: {name}, {pattern}")

    def addonFromModule(self, name):
        return "Ankimon"

# Mock Card class to simulate Anki cards
class MockCard:
    """Mocks an Anki Card object, providing essential attributes and methods for testing reviewer behavior.
    """
    def __init__(self, card_id, question="Sample Question", answer="Sample Answer", note_type="Basic"):
        self.id = card_id
        self.question = question
        self.answer = answer
        self.note_type = note_type
        self.queue = 0  # New card
        self.type = 0   # New card type
        self.due = 1
        self.ivl = 0    # Interval
        self.factor = 2500  # Ease factor
        self.reps = 0   # Number of reviews
        self.lapses = 0
        self.left = 0
        self.odue = 0
        self.odid = 0
        self.flags = 0
        self.data = ""

    def q(self):
        """Return question HTML"""
        return f"<div class='card'><h2>{self.question}</h2></div>"

    def a(self):
        """Return answer HTML"""
        return f"<div class='card'><h2>{self.question}</h2><hr><p>{self.answer}</p></div>"

class PureMockQWebEngineSettings:
    """A pure Python mock for PyQt6.QtWebEngineWidgets.QWebEngineSettings.
    Used in headless mode to avoid actual QtWebEngine dependency.
    """
    def __init__(self):
        logging.debug("PureMockQWebEngineSettings initialized.")
    def setFullScreenSupportEnabled(self, enabled):
        logging.debug(f"PureMockQWebEngineSettings: setFullScreenSupportEnabled({enabled}) called.")

class PureMockQWebEnginePage:
    """A pure Python mock for PyQt6.QtWebEngineWidgets.QWebEnginePage.
    Used in headless mode to avoid actual QtWebEngine dependency.
    """
    def __init__(self):
        logging.debug("PureMockQWebEnginePage initialized.")
        self._settings = PureMockQWebEngineSettings()
    def settings(self):
        logging.debug("PureMockQWebEnginePage: settings() called.")
        return self._settings
    def eval(self, js_code):
        logging.debug(f"PureMockQWebEnginePage.eval called with: {js_code[:100]}...") # Print first 100 chars of JS

class PureMockQWebEngineView:
    """A pure Python mock for PyQt6.QtWebEngineWidgets.QWebEngineView.
    Used in headless mode to avoid actual QtWebEngine dependency.
    """
    def __init__(self):
        logging.debug("PureMockQWebEngineView initialized.")
        self._page = PureMockQWebEnginePage()
    def page(self):
        logging.debug("PureMockQWebEngineView: page() called.")
        return self._page
    def setHtml(self, html_content):
        logging.debug(f"PureMockQWebEngineView.setHtml called with: {html_content[:100]}...") # Print first 100 chars of HTML
    def setMinimumHeight(self, height):
        logging.debug(f"PureMockQWebEngineView.setMinimumHeight({height}) called.")

# Enhanced MockReviewerWindow with QWebEngineView and card simulation
class MockReviewerWindow(QDialog):
    """A mock Anki reviewer window, simulating card display and answer functionality.
    Integrates with QWebEngineView (or PureMockQWebEngineView in headless mode) to render card content.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mock Anki Reviewer")
        self.setGeometry(200, 200, 800, 600)
        self.layout = QVBoxLayout(self)

        # Use QWebEngineView or PureMockQWebEngineView based on mode
        global is_headless_file_mode # Access the global flag
        if is_headless_file_mode:
            self.web = PureMockQWebEngineView()
        else:
            self.web = QWebEngineView()

        self.web.setMinimumHeight(400)
        self.layout.addWidget(self.web)

        # Answer buttons layout
        self.answer_buttons_layout = QHBoxLayout()
        self.again_btn = QPushButton("Again (1)")
        self.hard_btn = QPushButton("Hard (2)")
        self.good_btn = QPushButton("Good (3)")
        self.easy_btn = QPushButton("Easy (4)")

        # Style buttons
        for btn in [self.again_btn, self.hard_btn, self.good_btn, self.easy_btn]:
            btn.setMinimumHeight(40)

        self.answer_buttons_layout.addWidget(self.again_btn)
        self.answer_buttons_layout.addWidget(self.hard_btn)
        self.answer_buttons_layout.addWidget(self.good_btn)
        self.answer_buttons_layout.addWidget(self.easy_btn)
        self.layout.addLayout(self.answer_buttons_layout)

        # Connect buttons to answer function
        self.again_btn.clicked.connect(lambda: self.answer_card(1))
        self.hard_btn.clicked.connect(lambda: self.answer_card(2))
        self.good_btn.clicked.connect(lambda: self.answer_card(3))
        self.easy_btn.clicked.connect(lambda: self.answer_card(4))

        # Show answer button (hidden initially)
        self.show_answer_btn = QPushButton("Show Answer")
        self.show_answer_btn.setMinimumHeight(40)
        self.show_answer_btn.clicked.connect(self.show_answer)
        self.layout.addWidget(self.show_answer_btn)

        # Card simulation
        self.current_card_index = 0
        self.showing_answer = False
        self.cards = [
            MockCard(1, "What is the capital of France?", "Paris"),
            MockCard(2, "What is 2 + 2?", "4"),
            MockCard(3, "What is the largest planet?", "Jupiter"),
            MockCard(4, "What year did World War II end?", "1945"),
            MockCard(5, "What is the speed of light?", "299,792,458 m/s"),
        ]

        # Hide answer buttons initially
        self.hide_answer_buttons()

        # Load first card
        self.load_current_card()

    def hide_answer_buttons(self):
        """Hide answer buttons and show 'Show Answer' button"""
        for btn in [self.again_btn, self.hard_btn, self.good_btn, self.easy_btn]:
            if hasattr(btn, 'hide'): btn.hide()
        if hasattr(self.show_answer_btn, 'show'): self.show_answer_btn.show()

    def show_answer_buttons(self):
        """Show answer buttons and hide 'Show Answer' button"""
        for btn in [self.again_btn, self.hard_btn, self.good_btn, self.easy_btn]:
            if hasattr(btn, 'show'): btn.show()
        if hasattr(self.show_answer_btn, 'hide'): self.show_answer_btn.hide()

    def load_current_card(self):
        """Load the current card's question"""
        if self.current_card_index < len(self.cards):
            card = self.cards[self.current_card_index]
            self.current_card = card
            self.showing_answer = False

            # Set HTML content
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    h2 {{ color: #333; margin-top: 0; }}
                    hr {{ border: none; border-top: 2px solid #ddd; margin: 20px 0; }}
                    p {{ font-size: 16px; line-height: 1.5; }}
                    .card-info {{ font-size: 12px; color: #666; margin-top: 15px; }}
                </style>
            </head>
            <body>
                {card.q()}
                <div class="card-info">Card {self.current_card_index + 1} of {len(self.cards)} | Type: {card.note_type}</div>
            </body>
            </html>
            """
            if hasattr(self.web, 'setHtml'): self.web.setHtml(html_content)
            self.hide_answer_buttons()

            # Trigger reviewer_did_show_question hook
            logging.debug(f"Triggering reviewer_did_show_question for card {card.id}")
            if 'mock_aqt_gui_hooks_module' in globals():
                for func in mock_aqt_gui_hooks_module.reviewer_did_show_question:
                    try:
                        func(card)
                    except Exception as e:
                        logging.debug(f"Error in reviewer_did_show_question hook: {e}")

        else:
            # No more cards
            if hasattr(self.web, 'setHtml'): self.web.setHtml("<div class='card'><h2>No more cards!</h2><p>Review session complete.</p></div>")
            self.hide_answer_buttons()
            if hasattr(self.show_answer_btn, 'hide'): self.show_answer_btn.hide()

    def show_answer(self):
        """Show the answer for the current card"""
        if hasattr(self, 'current_card') and not self.showing_answer:
            card = self.current_card
            self.showing_answer = True

            # Set HTML content with answer
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                    .card {{ background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                    h2 {{ color: #333; margin-top: 0; }}
                    hr {{ border: none; border-top: 2px solid #ddd; margin: 20px 0; }}
                    p {{ font-size: 16px; line-height: 1.5; }}
                    .card-info {{ font-size: 12px; color: #666; margin-top: 15px; }}
                </style>
            </head>
            <body>
                {card.a()}
                <div class="card-info">Card {self.current_card_index + 1} of {len(self.cards)} | Type: {card.note_type}</div>
            </body>
            </html>
            """
            if hasattr(self.web, 'setHtml'): self.web.setHtml(html_content)
            self.show_answer_buttons()

            # Trigger reviewer_did_show_answer hook
            logging.debug(f"Triggering reviewer_did_show_answer for card {card.id}")
            if 'mock_aqt_gui_hooks_module' in globals():
                for func in mock_aqt_gui_hooks_module.reviewer_did_show_answer:
                    try:
                        func(card)
                    except Exception as e:
                        logging.debug(f"Error in reviewer_did_show_answer hook: {e}")

    def answer_card(self, ease):
        """Answer the current card with the given ease"""
        if hasattr(self, 'current_card'):
            card = self.current_card
            logging.debug(f"Card {card.id} answered with ease: {ease}")

            # Trigger reviewer_did_answer_card hook
            if 'mock_aqt_gui_hooks_module' in globals():
                for func in mock_aqt_gui_hooks_module.reviewer_did_answer_card:
                    try:
                        func(None, card, ease)  # Pass reviewer, card, ease
                    except Exception as e:
                        logging.debug(f"Error in reviewer_did_answer_card hook: {e}")

            # Move to next card
            self.current_card_index += 1

            # Small delay before loading next card for visual feedback
            if hasattr(QTimer, 'singleShot'): QTimer.singleShot(300, self.load_current_card)

# Create mock objects
class MockCollection:
    """Mocks Anki's Collection object. Currently a placeholder.
    """
    def __init__(self):
        pass

class MockAnkiHooks:
    """Mocks Anki's hooks module, allowing add-ons to register and trigger hooks.
    """
    def addHook(self, *args, **kwargs):
        pass
    def wrap(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MockGuiHooks:
    """Mocks Anki's gui_hooks module, providing lists to register hook functions.
    """
    def __init__(self):
        self.reviewer_will_end = []
        self.reviewer_did_answer_card = []
        self.theme_did_change = []
        self.reviewer_did_show_question = []
        self.reviewer_did_show_answer = []
        self.webview_will_set_content = []
        self.addon_config_editor_will_display_json = []
        self.reviewer_will_answer_card = []
        self.profile_did_open = []

    def addHook(self, *args, **kwargs):
        pass

class MockQWebEngineSettings:
    """A basic mock for PyQt6.QtWebEngineWidgets.QWebEngineSettings.
    Used when a full GUI is present but specific settings are not critical for the test.
    """
    def __init__(self):
        pass

class MockQWebEnginePage:
    def __init__(self):
        pass

class MockUtils:
    def __init__(self):
        pass
    def downArrow(self, *args, **kwargs):
        pass
    def showWarning(self, *args, **kwargs):
        logging.debug(f"showWarning called: {args}")
    def showInfo(self, *args, **kwargs):
        logging.debug(f"showInfo called: {args}")
    def tr(self, *args, **kwargs):
        return args[0] if args else ""
    def tooltip(self, *args, **kwargs):
        logging.debug(f"tooltip called: {args}")
    def qconnect(self, *args, **kwargs):
        logging.debug(f"qconnect called: {args}")
    def QWebEngineSettings(self, *args, **kwargs):
        return MockQWebEngineSettings()
    def QWebEnginePage(self, *args, **kwargs):
        return MockQWebEnginePage()
    def QWebEngineView(self, *args, **kwargs):
        global is_headless_file_mode
        return PureMockQWebEngineView() if is_headless_file_mode else QWebEngineView()

# Enhanced MockReviewer that integrates with MockReviewerWindow
class MockQWebEnginePage:
    def __init__(self):
        pass
    def eval(self, js_code):
        logging.debug(f"MockQWebEnginePage.eval called with: {js_code[:100]}...") # Print first 100 chars of JS

class MockQWebEngineView:
    def __init__(self):
        self._page = MockQWebEnginePage()
    def page(self):
        return self._page
    def setHtml(self, html_content):
        logging.debug(f"MockQWebEngineView.setHtml called with: {html_content[:100]}...") # Print first 100 chars of HTML
    def setMinimumHeight(self, height):
        pass # No-op for mock

# Enhanced MockReviewer that integrates with MockReviewerWindow
class MockReviewer:
    _shortcutKeys = {}
    _linkHandler = lambda self, url, _old: True

    def __init__(self):
        global is_headless_file_mode
        self.web = PureMockQWebEngineView() if is_headless_file_mode else QWebEngineView()  # Add web attribute
        self.reviewer_window = None  # Will be set later
        self.card = None  # Current card

    def show(self):
        """Show the reviewer window"""
        logging.debug("MockReviewer: show() called.")
        if self.reviewer_window and hasattr(self.reviewer_window, 'show'):
            self.reviewer_window.show()

    def setCard(self, card):
        """Set the current card"""
        self.card = card
        logging.debug(f"MockReviewer.setCard called with card: {card}")

    def showQuestion(self):
        logging.debug("MockReviewer: showQuestion() called.")
        if self.reviewer_window and hasattr(self.reviewer_window, 'load_current_card'):
            self.reviewer_window.load_current_card() # This will show the question

    def showAnswer(self):
        logging.debug("MockReviewer: showAnswer() called.")
        if self.reviewer_window and hasattr(self.reviewer_window, 'show_answer'):
            self.reviewer_window.show_answer() # This will show the answer

    def answerCard(self, ease):
        logging.debug(f"MockReviewer: answerCard({ease}) called.")
        if self.reviewer_window and hasattr(self.reviewer_window, 'answer_card'):
            self.reviewer_window.answer_card(ease) # This will answer the card and move to next

class MockAnkiWebView:
    def __init__(self):
        pass

class MockWebContent:
    def __init__(self):
        pass

class MockSoundOrVideoTag:
    def __init__(self):
        pass

class MockAVPlayer:
    def __init__(self):
        pass

class MockAnkiUtils:
    def __init__(self):
        pass
    def is_win(self):
        return sys.platform.startswith("win")
    def isWin(self):
        return self.is_win()

class MockAnkiBuildInfo:
    def __init__(self):
        self.version = "2.1.66"

class MockProfileManager:
    def __init__(self):
        self.name = "test_profile"

class MockThemeManager:
    def __init__(self):
        self.night_mode = False

# Mock aqt.dialogs for handling dialog opening
class MockDialogManager:
    def __init__(self):
        self.dialogs = {}

    def open(self, name, parent, *args, **kwargs):
        logging.debug(f"aqt.dialogs.open called: {name}, parent: {parent}, args: {args}, kwargs: {kwargs}")
        # Return a mock dialog or handle specific dialog types
        return MockDialog(name)

class MockDialog:
    def __init__(self, name):
        self.name = name
        logging.debug(f"MockDialog created: {name}")

    def show(self):
        logging.debug(f"MockDialog.show called: {self.name}")

    def exec(self):
        logging.debug(f"MockDialog.exec called: {self.name}")
        return 0

class MockMenuBar(QMenuBar):
    def __init__(self):
        super().__init__()
    def addMenu(self, menu):
        return super().addMenu(menu)

class MockForm:
    def __init__(self):
        self.menubar = MockMenuBar()
        self.centralwidget = QWidget()
    def setupUi(self, main_window):
        main_window.setMenuBar(self.menubar)
        main_window.setCentralWidget(self.centralwidget)

class MockMainWindow(QMainWindow):
    """Mocks Anki's main window (mw), providing core Anki objects."""
    def __init__(self):
        super().__init__()
        self.col = MockCollection()
        self.addonManager = MockAddonManager()
        self.pm = MockProfileManager()
        self.form = MockForm()
        self.form.setupUi(self)
        
        if hasattr(self, 'setGeometry'): # Only if it's a real Qt widget
            self.setGeometry(100, 100, 800, 600)

        # Create and integrate MockReviewer with MockReviewerWindow
        self.reviewer = MockReviewer()
        self.reviewer_window = MockReviewerWindow(self)
        self.reviewer.reviewer_window = self.reviewer_window

    def message_box(self, text):
        if hasattr(QMessageBox, 'setText'):
            msg = QMessageBox()
            msg.setText(text)
            msg.exec()
        else:
            logging.info(f"MockMessageBox: {text}") # Log message in headless mode

# Additional Mock Classes for Ankimon addon
class MockShowInfoLogger:
    def __init__(self):
        pass
    def log(self, *args, **kwargs):
        logging.debug(f"Logger.log: {args}")
    def log_and_showinfo(self, *args, **kwargs):
        logging.debug(f"Logger.log_and_showinfo: {args}")
    def toggle_log_window(self):
        logging.debug("Logger.toggle_log_window called")

class MockTranslator:
    def __init__(self, language):
        self.language = language
    def translate(self, key, **kwargs):
        return f"Translated_{key}"

class MockReviewerManager:
    def __init__(self, settings_obj, main_pokemon, enemy_pokemon, ankimon_tracker):
        self.settings = settings_obj
        self.main_pokemon = main_pokemon
        self.enemy_pokemon = enemy_pokemon
        self.ankimon_tracker = ankimon_tracker
        self.life_bar_injected = False
        self.seconds = 0
        self.myseconds = 0
        global is_headless_file_mode
        self.web = PureMockQWebEngineView() if is_headless_file_mode else QWebEngineView() # Use our mock QWebEngineView

    def update_life_bar(self, reviewer, card, ease):
        # This is a simplified mock of the actual update_life_bar logic
        # It focuses on the eval call that was causing the error
        js_code = "if(window.__ankimonHud) window.__ankimonHud.update('mock_html', 'mock_css');"
        if hasattr(reviewer.web.page(), 'eval'):
            reviewer.web.page().eval(js_code)
            logging.debug("MockReviewerManager.update_life_bar called and eval simulated.")
        else:
            logging.debug("MockReviewerManager.update_life_bar called, eval skipped (headless).")

class MockTestWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'setWindowTitle'): self.setWindowTitle("Mock Ankimon Window")
        if hasattr(self, 'setGeometry'): self.setGeometry(300, 300, 800, 600)
        if hasattr(self, 'setLayout'):
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("This is a mock Ankimon window."))
            self.setLayout(layout)

    def open_dynamic_window(self):
        logging.debug("MockTestWindow.open_dynamic_window called")
        if hasattr(self, 'show'): self.show()

class MockPokemonObject:
    def __init__(self, *args, **kwargs):
        self.name = kwargs.get("name", "MockPokemon")
        self.id = kwargs.get("id", 1)
        self.level = kwargs.get("level", 1)
        self.ability = kwargs.get("ability", "mock_ability")
        self.type = kwargs.get("type", ["Normal"])
        self.stats = kwargs.get("stats", {})
        self.ev = kwargs.get("ev", {})
        self.iv = kwargs.get("iv", {})
        self.attacks = kwargs.get("attacks", [])
        self.base_experience = kwargs.get("base_experience", 0)
        self.growth_rate = kwargs.get("growth_rate", "medium")
        self.current_hp = kwargs.get("current_hp", 100)
        self.gender = kwargs.get("gender", "N")
        self.shiny = kwargs.get("shiny", False)
        self.individual_id = kwargs.get("individual_id", "mock_id")
        self.status = kwargs.get("status", None)
        self.volatile_status = kwargs.get("volatile_status", set())
        self.xp = kwargs.get("xp", 0)
        self.nickname = kwargs.get("nickname", "")
        self.friendship = kwargs.get("friendship", 0)
        self.pokemon_defeated = kwargs.get("pokemon_defeated", 0)
        self.everstone = kwargs.get("everstone", False)
        self.mega = kwargs.get("mega", False)
        self.special_form = kwargs.get("special_form", None)
        self.evos = kwargs.get("evos", [])
        self.tier = kwargs.get("tier", None)
        self.captured_date = kwargs.get("captured_date", None)
        self.is_favorite = kwargs.get("is_favorite", False)
        self.held_item = kwargs.get("held_item", None)
    def to_dict(self): return {}
    @staticmethod
    def calc_stat(*args, **kwargs): return 100

class MockTrainerCard:
    def __init__(self, logger, main_pokemon, settings_obj, trainer_name, badge_count, trainer_id, level=1, xp=0, achievements=None, team="", image_path="", league="unranked"):
        self.logger = logger
        self.main_pokemon = main_pokemon
        self.settings_obj = settings_obj
        self.trainer_name = trainer_name
        self.badge_count = badge_count
        self.trainer_id = trainer_id
        self.level = level
        self.xp = xp
        self.achievements = achievements if achievements else []
        self.team = team
        self.image_path = image_path
        self.league = league
        self.cash = 0
        self.favorite_pokemon = ""
        self.highest_level = 0
    def get_highest_level_pokemon(self): return "None"
    def highest_pokemon_level(self): return 0
    def add_achievement(self, achievement): pass
    def set_team(self, team_pokemons): pass
    def display_card_data(self): return {}
    def xp_for_next_level(self): return 100
    def on_level_up(self): pass
    def gain_xp(self, tier, allow_to_choose_move=False): pass
    def check_level_up(self): pass

# Additional simplified mock classes
class MockDataHandlerWindow:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): logging.debug("DataHandlerWindow.show_window called")

class MockSettingsWindow:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): logging.debug("SettingsWindow.show_window called")

class MockPokemonShopManager:
    def __init__(self, *args, **kwargs): pass
    def toggle_window(self): logging.debug("PokemonShopManager.toggle_window called")

class MockPokedex(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'setWindowTitle'): self.setWindowTitle("Mock Pokedex")
        if hasattr(self, 'setGeometry'): self.setGeometry(300, 300, 600, 400)
        if hasattr(self, 'setLayout'):
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("This is a mock Pokedex window."))
            self.setLayout(layout)

    def show(self):
        logging.debug("MockPokedex.show called")
        if hasattr(self, 'exec'): self.exec()

class MockAchievementWindow:
    def __init__(self):
        pass
    def show_window(self): logging.debug("AchievementWindow.show_window called")

class MockAnkimonTrackerWindow:
    def __init__(self, *args, **kwargs): pass
    def toggle_window(self): logging.debug("AnkimonTrackerWindow.toggle_window called")

class MockLicense:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): logging.debug("License.show_window called")

class MockCredits:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): logging.debug("Credits.show_window called")

class MockTableWidget:
    def __init__(self, *args, **kwargs): pass
    def show_eff_chart(self): logging.debug("TableWidget.show_eff_chart called")

class MockIDTableWidget:
    def __init__(self, *args, **kwargs): pass
    def show_gen_chart(self): logging.debug("IDTableWidget.show_gen_chart called")

class MockVersionDialog:
    def __init__(self, *args, **kwargs): pass
    def open(self): logging.debug("VersionDialog.open called")

class MockDataHandler:
    def __init__(self, *args, **kwargs): pass

class MockEnemyPokemon:
    def __init__(self):
        self.type = ["Normal"]

class MockItemBagPath:
    def __init__(self):
        pass

class MockAchievements:
    def __init__(self):
        pass

class MockStarterWindow:
    def __init__(self):
        pass
    def display_fossil_pokemon(self, *args, **kwargs):
        logging.debug("StarterWindow.display_fossil_pokemon called")

class MockEvoWindow:
    def __init__(self):
        pass
    def display_pokemon_evo(self, *args, **kwargs):
        logging.debug("EvoWindow.display_pokemon_evo called")

class MockPokemonPC(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self, 'setWindowTitle'): self.setWindowTitle("Mock Pokémon PC")
        if hasattr(self, 'setGeometry'): self.setGeometry(300, 300, 600, 400)
        if hasattr(self, 'setLayout'):
            layout = QVBoxLayout(self)
            layout.addWidget(QLabel("This is a mock Pokémon PC window."))
            self.setLayout(layout)

    def show(self):
        logging.debug("MockPokemonPC.show called")
        if hasattr(self, 'exec'): self.exec()


# Global references for mocks that need to be accessed by internal mock logic (e.g., hooks)
mock_aqt_qt_module = None
mock_aqt_reviewer_module = None
mock_aqt_utils_module = None
mock_aqt_gui_hooks_module = None
mock_aqt_webview_module = None
mock_aqt_sound_module = None
mock_aqt_theme_module = None
mock_anki_hooks_module = None
mock_anki_collection_module = None
mock_anki_utils_module = None
mock_anki_buildinfo_module = None
mock_aqt_dialogs_module = None
mock_aqt_module = None # The top-level aqt mock module

def setup_test_environment(is_headless_mode=False):
    """
    Sets up the test environment by adding Ankimon's source to sys.path
    and creating mock Anki/aqt modules in sys.modules.

    Args:
        is_headless_mode (bool): If True, use pure Python mocks where possible
                                 to avoid PyQt6 dependencies for webviews.

    Returns:
        tuple: (mw_instance, dialogs_manager)
    """
    global mock_aqt_qt_module, mock_aqt_reviewer_module, mock_aqt_utils_module, \
           mock_aqt_gui_hooks_module, mock_aqt_webview_module, mock_aqt_sound_module, \
           mock_aqt_theme_module, mock_anki_hooks_module, mock_anki_collection_module, \
           mock_anki_utils_module, mock_anki_buildinfo_module, mock_aqt_dialogs_module, \
           mock_aqt_module, is_headless_file_mode # Access global variable

    is_headless_file_mode = is_headless_mode # Update global flag based on call

    # Add the Ankimon addon directory to the Python path
    ankimon_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    if ankimon_src_path not in sys.path:
        sys.path.insert(0, ankimon_src_path)
    logging.debug(f"sys.path updated to include: {ankimon_src_path}")

    # --- Crucial: Remove existing Anki/Aqt modules from sys.modules ---
    # This ensures a clean mock environment, preventing interference from actual Anki modules
    # if the script is run within an Anki context or if modules were previously loaded.
    for module_name in [
        'aqt', 'anki', 'aqt.qt', 'aqt.reviewer', 'aqt.utils', 'aqt.gui_hooks',
        'aqt.webview', 'aqt.sound', 'aqt.theme', 'anki.hooks', 'anki.collection',
        'anki.utils', 'anki.buildinfo', 'aqt.dialogs'
    ]:
        if module_name in sys.modules:
            del sys.modules[module_name]
            logging.debug(f"Removed existing module from sys.modules: {module_name}")

    # --- Proper mocking of anki and aqt modules ---

    # Mock aqt.qt module
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
    logging.debug("Mocked 'aqt.qt' module.")

    # Mock aqt.reviewer module
    mock_aqt_reviewer_module = ModuleType('aqt.reviewer')
    mock_aqt_reviewer_module.Reviewer = MockReviewer
    sys.modules['aqt.reviewer'] = mock_aqt_reviewer_module
    logging.debug("Mocked 'aqt.reviewer' module.")

    # Mock aqt.utils module
    mock_aqt_utils_module = ModuleType('aqt.utils')
    mock_aqt_utils_instance = MockUtils()
    mock_aqt_utils_module.downArrow = mock_aqt_utils_instance.downArrow
    mock_aqt_utils_module.showWarning = mock_aqt_utils_instance.showWarning
    mock_aqt_utils_module.showInfo = mock_aqt_utils_instance.showInfo
    mock_aqt_utils_module.tr = mock_aqt_utils_instance.tr
    mock_aqt_utils_module.tooltip = mock_aqt_utils_instance.tooltip
    mock_aqt_utils_module.qconnect = mock_aqt_utils_instance.qconnect
    mock_aqt_utils_module.QWebEngineSettings = MockQWebEngineSettings
    mock_aqt_utils_module.QWebEnginePage = PureMockQWebEnginePage if is_headless_mode else MockQWebEnginePage # Use real QtWebEnginePage if GUI
    mock_aqt_utils_module.QWebEngineView = PureMockQWebEngineView if is_headless_mode else QWebEngineView
    sys.modules['aqt.utils'] = mock_aqt_utils_module
    logging.debug("Mocked 'aqt.utils' module.")

    # Mock aqt.gui_hooks module
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
    logging.debug("Mocked 'aqt.gui_hooks' module.")


    # Mock aqt.webview module
    mock_aqt_webview_module = ModuleType('aqt.webview')
    mock_aqt_webview_module.WebContent = MockWebContent
    mock_aqt_webview_module.AnkiWebView = PureMockQWebEngineView if is_headless_mode else QWebEngineView
    sys.modules['aqt.webview'] = mock_aqt_webview_module
    logging.debug("Mocked 'aqt.webview' module.")

    # Mock aqt.sound module
    mock_aqt_sound_module = ModuleType('aqt.sound')
    mock_aqt_sound_module.SoundOrVideoTag = MockSoundOrVideoTag
    mock_aqt_sound_module.AVPlayer = MockAVPlayer
    sys.modules['aqt.sound'] = mock_aqt_sound_module
    logging.debug("Mocked 'aqt.sound' module.")

    # Mock aqt.theme module
    mock_aqt_theme_module = ModuleType('aqt.theme')
    mock_aqt_theme_module.theme_manager = MockThemeManager()
    sys.modules['aqt.theme'] = mock_aqt_theme_module
    logging.debug("Mocked 'aqt.theme' module.")

    # Mock anki.hooks module
    mock_anki_hooks_module = ModuleType('anki.hooks')
    mock_anki_hooks_instance = MockAnkiHooks()
    mock_anki_hooks_module.addHook = mock_anki_hooks_instance.addHook
    mock_anki_hooks_module.wrap = mock_anki_hooks_instance.wrap
    sys.modules['anki.hooks'] = mock_anki_hooks_module
    logging.debug("Mocked 'anki.hooks' module.")

    # Mock anki.collection module
    mock_anki_collection_module = ModuleType('anki.collection')
    mock_anki_collection_module.Collection = MockCollection
    sys.modules['anki.collection'] = mock_anki_collection_module
    logging.debug("Mocked 'anki.collection' module.")

    # Mock anki.utils module
    mock_anki_utils_module = ModuleType('anki.utils')
    mock_anki_utils_instance = MockAnkiUtils()
    mock_anki_utils_module.is_win = mock_anki_utils_instance.is_win
    mock_anki_utils_module.isWin = mock_anki_utils_instance.isWin
    sys.modules['anki.utils'] = mock_anki_utils_module
    logging.debug("Mocked 'anki.utils' module.")

    # Mock anki.buildinfo module
    mock_anki_buildinfo_module = ModuleType('anki.buildinfo')
    mock_anki_buildinfo_instance = MockAnkiBuildInfo()
    mock_anki_buildinfo_module.version = mock_anki_buildinfo_instance.version
    sys.modules['anki.buildinfo'] = mock_anki_buildinfo_module
    logging.debug("Mocked 'anki.buildinfo' module.")

    # Mock anki module (as a package)
    mock_anki_module = ModuleType('anki')
    mock_anki_module.__path__ = [] # Essential for package recognition
    mock_anki_module.hooks = mock_anki_hooks_module
    mock_anki_module.collection = mock_anki_collection_module
    mock_anki_module.utils = mock_anki_utils_module
    mock_anki_module.buildinfo = mock_anki_buildinfo_module
    sys.modules['anki'] = mock_anki_module
    logging.debug("Mocked top-level 'anki' module.")

    # Create mw_instance and dialogs_manager after all mock modules are defined
    mw_instance = MockMainWindow()
    dialogs_manager = MockDialogManager()

    # Mock aqt.dialogs module
    mock_aqt_dialogs_module = ModuleType('aqt.dialogs')
    mock_aqt_dialogs_module.open = dialogs_manager.open
    sys.modules['aqt.dialogs'] = mock_aqt_dialogs_module
    logging.debug("Mocked 'aqt.dialogs' module.")

    # Mock aqt module (as a package)
    mock_aqt_module = ModuleType('aqt')
    mock_aqt_module.__path__ = [] # Essential for package recognition
    mock_aqt_module.mw = mw_instance
    mock_aqt_module.gui_hooks = mock_aqt_gui_hooks_module
    mock_aqt_module.utils = mock_aqt_utils_module
    mock_aqt_module.qt = mock_aqt_qt_module
    mock_aqt_module.reviewer = mock_aqt_reviewer_module
    mock_aqt_module.webview = mock_aqt_webview_module
    mock_aqt_module.sound = mock_aqt_sound_module
    mock_aqt_module.theme = mock_aqt_theme_module
    mock_aqt_module.dialogs = mock_aqt_dialogs_module
    mock_aqt_module.qconnect = MockUtils().qconnect # This might be redundant if aqt.qt.qconnect is used
    mock_aqt_module.QDialog = QDialog # Direct access for convenience
    mock_aqt_module.QVBoxLayout = QVBoxLayout # Direct access for convenience
    mock_aqt_module.QWebEngineView = QWebEngineView # Direct access for convenience
    sys.modules['aqt'] = mock_aqt_module
    logging.debug("Mocked top-level 'aqt' module.")
    logging.info("Anki/aqt mock environment set up successfully.")

    return mw_instance, dialogs_manager, mock_aqt_gui_hooks_module

def run_self_tests(app_instance, is_headless_test=False):
    """
    Runs a series of self-tests to verify the integrity of the test environment setup.
    """
    logging.info("Running self-tests for Ankimon Test Environment...")
    all_tests_passed = True

    # Temporarily redirect logging to capture output for specific tests
    log_capture_string = io.StringIO()
    # Use a new handler for capturing, without affecting the main logging
    ch = logging.StreamHandler(log_capture_string)
    ch.setLevel(logging.ERROR)
    temp_logger = logging.getLogger('test_logger')
    temp_logger.addHandler(ch)
    temp_logger.propagate = False # Prevent logs from going to main logger during capture

    # Test 1: sys.path setup
    expected_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
    if expected_path in sys.path:
        logging.info(f"TEST PASSED: sys.path contains Ankimon source directory: {expected_path}")
    else:
        logging.error(f"TEST FAILED: sys.path does not contain Ankimon source directory. Expected: {expected_path}")
        all_tests_passed = False

    # Test 2: QApplication presence (if not headless)
    if not is_headless_test:
        if app_instance and isinstance(app_instance, QApplication):
            logging.info("TEST PASSED: QApplication instance is present.")
        else:
            logging.error("TEST FAILED: QApplication instance is NOT present.")
            all_tests_passed = False
    else:
        if isinstance(app_instance, DummyQApplication):
            logging.info("TEST PASSED: DummyQApplication instance is present in headless mode.")
        else:
            logging.error("TEST FAILED: DummyQApplication instance is NOT present in headless mode.")
            all_tests_passed = False

    # Test 3: Mocks presence and basic attributes
    # The actual 'QApplication' attribute is on aqt.qt, not aqt.qt.QApplication itself
    expected_mocks = {
        'aqt.qt': ['QDialog', 'QWidget', 'QApplication'], # QApplication here refers to the class, not instance
        'aqt.reviewer': ['Reviewer'],
        'aqt.utils': ['showWarning', 'showInfo', 'QWebEngineView'],
        'aqt.gui_hooks': ['reviewer_did_show_question', 'reviewer_did_answer_card'],
        'aqt.webview': ['WebContent', 'AnkiWebView'],
        'aqt.sound': ['SoundOrVideoTag', 'AVPlayer'],
        'aqt.theme': ['theme_manager'],
        'anki.hooks': ['addHook', 'wrap'],
        'anki.collection': ['Collection'],
        'anki.utils': ['is_win', 'isWin'],
        'anki.buildinfo': ['version'],
        'aqt.dialogs': ['open'],
        'aqt': ['mw', 'gui_hooks', 'utils', 'qt', 'reviewer', 'webview', 'sound', 'theme', 'dialogs']
    }

    for module_name, attributes in expected_mocks.items():
        if module_name in sys.modules:
            logging.info(f"TEST PASSED: Mock module '{module_name}' is present in sys.modules.")
            mock_module = sys.modules[module_name]
            for attr in attributes:
                if hasattr(mock_module, attr):
                    # Special check for QApplication as it's a class
                    if attr == 'QApplication' and module_name == 'aqt.qt':
                        if is_headless_test:
                            if hasattr(mock_module, 'QApplication') and not isinstance(mock_module.QApplication, type(QApplication)):
                                logging.info(f"  TEST PASSED: Dummy QApplication class found in 'aqt.qt'.")
                            else:
                                logging.error(f"  TEST FAILED: Dummy QApplication class not correctly mocked in headless 'aqt.qt'.")
                                all_tests_passed = False
                        else:
                            if hasattr(mock_module, 'QApplication') and isinstance(mock_module.QApplication, type(QApplication)):
                                logging.info(f"  TEST PASSED: Real QApplication class found in 'aqt.qt'.")
                            else:
                                logging.error(f"  TEST FAILED: Real QApplication class not correctly provided in GUI 'aqt.qt'.")
                                all_tests_passed = False
                    else:
                        logging.info(f"  TEST PASSED: Attribute '{attr}' found in '{module_name}'.")
                else:
                    logging.error(f"  TEST FAILED: Attribute '{attr}' not found in '{module_name}'.")
                    all_tests_passed = False
        else:
            logging.error(f"TEST FAILED: Mock module '{module_name}' is NOT present in sys.modules.")
            all_tests_passed = False

    # Test 4: Error handling for missing/corrupt configs (using ConfigError)
    temp_dir = Path(tempfile.gettempdir())

    # Test missing JSON file with ConfigError
    temp_missing_file = temp_dir / "non_existent_file_for_test.json"
    try:
        load_ankimon_json(temp_missing_file)
        temp_logger.error(f"TEST FAILED: load_ankimon_json did NOT raise ConfigError for missing file: {temp_missing_file}")
        all_tests_passed = False
    except ConfigError as e:
        if f"Required JSON file not found: {temp_missing_file}" in str(e):
            logging.info("TEST PASSED: load_ankimon_json raises ConfigError for missing file.")
        else:
            temp_logger.error(f"TEST FAILED: load_ankimon_json raised wrong ConfigError for missing file: {e}")
            all_tests_passed = False
    except Exception as e:
        temp_logger.error(f"TEST FAILED: load_ankimon_json raised unexpected error for missing file: {type(e).__name__} - {e}")
        all_tests_passed = False
    log_capture_string.truncate(0)
    log_capture_string.seek(0)

    # Test corrupt JSON file with ConfigError
    temp_corrupt_file = temp_dir / "corrupt_config_for_test.json"
    with open(temp_corrupt_file, "w") as f:
        f.write("{invalid json")
    try:
        load_ankimon_json(temp_corrupt_file)
        temp_logger.error(f"TEST FAILED: load_ankimon_json did NOT raise ConfigError for corrupt JSON: {temp_corrupt_file}")
        all_tests_passed = False
    except ConfigError as e:
        if f"Corrupt JSON in file: {temp_corrupt_file}" in str(e):
            logging.info("TEST PASSED: load_ankimon_json raises ConfigError for corrupt JSON.")
        else:
            temp_logger.error(f"TEST FAILED: load_ankimon_json raised wrong ConfigError for corrupt JSON: {e}")
            all_tests_passed = False
    except Exception as e:
        temp_logger.error(f"TEST FAILED: load_ankimon_json raised unexpected error for corrupt JSON: {type(e).__name__} - {e}")
        all_tests_passed = False
    finally:
        if temp_corrupt_file.exists():
            temp_corrupt_file.unlink() # Clean up
    log_capture_string.truncate(0)
    log_capture_string.seek(0)

    # Remove the temporary log handler
    temp_logger.removeHandler(ch)

    if all_tests_passed:
        logging.info("All self-tests PASSED!")
        return True
    else:
        logging.error("Some self-tests FAILED!")
        # Print captured error logs if any failures occurred
        if log_capture_string.getvalue():
            logging.error("\n--- Captured Error Logs During Self-Tests ---")
            for line in log_capture_string.getvalue().splitlines():
                logging.error(line)
            logging.error("---------------------------------------------\n")
        return False

# --- End of proper mocking ---









# --- Crucial: Remove existing Anki/Aqt modules from sys.modules ---
for module_name in ['aqt', 'anki', 'aqt.qt', 'aqt.reviewer', 'aqt.utils', 'aqt.gui_hooks', 'aqt.webview', 'aqt.sound', 'aqt.theme', 'anki.hooks', 'anki.collection', 'anki.utils', 'anki.buildinfo', 'aqt.dialogs']:
    if module_name in sys.modules:
        del sys.modules[module_name]

# --- Proper mocking of anki and aqt modules ---

# Mock aqt.qt module
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

# Mock aqt.reviewer module
mock_aqt_reviewer_module = ModuleType('aqt.reviewer')
mock_aqt_reviewer_module.Reviewer = MockReviewer
sys.modules['aqt.reviewer'] = mock_aqt_reviewer_module

# Mock aqt.utils module
mock_aqt_utils_module = ModuleType('aqt.utils')
mock_aqt_utils_instance = MockUtils()
mock_aqt_utils_module.downArrow = mock_aqt_utils_instance.downArrow
mock_aqt_utils_module.showWarning = mock_aqt_utils_instance.showWarning
mock_aqt_utils_module.showInfo = mock_aqt_utils_instance.showInfo
mock_aqt_utils_module.tr = mock_aqt_utils_instance.tr
mock_aqt_utils_module.tooltip = mock_aqt_utils_instance.tooltip
mock_aqt_utils_module.qconnect = mock_aqt_utils_instance.qconnect
mock_aqt_utils_module.QWebEngineSettings = MockQWebEngineSettings
mock_aqt_utils_module.QWebEnginePage = MockQWebEnginePage
mock_aqt_utils_module.QWebEngineView = PureMockQWebEngineView if is_headless_file_mode else QWebEngineView
sys.modules['aqt.utils'] = mock_aqt_utils_module

# Mock aqt.gui_hooks module
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

# Mock aqt.webview module
mock_aqt_webview_module = ModuleType('aqt.webview')
mock_aqt_webview_module.WebContent = MockWebContent
mock_aqt_webview_module.AnkiWebView = PureMockQWebEngineView if is_headless_file_mode else QWebEngineView
sys.modules['aqt.webview'] = mock_aqt_webview_module

# Mock aqt.sound module
mock_aqt_sound_module = ModuleType('aqt.sound')
mock_aqt_sound_module.SoundOrVideoTag = MockSoundOrVideoTag
mock_aqt_sound_module.AVPlayer = MockAVPlayer
sys.modules['aqt.sound'] = mock_aqt_sound_module

# Mock aqt.theme module
mock_aqt_theme_module = ModuleType('aqt.theme')
mock_aqt_theme_module.theme_manager = MockThemeManager()
sys.modules['aqt.theme'] = mock_aqt_theme_module

# Mock anki.hooks module
mock_anki_hooks_module = ModuleType('anki.hooks')
mock_anki_hooks_instance = MockAnkiHooks()
mock_anki_hooks_module.addHook = mock_anki_hooks_instance.addHook
mock_anki_hooks_module.wrap = mock_anki_hooks_instance.wrap
sys.modules['anki.hooks'] = mock_anki_hooks_module

# Mock anki.collection module
mock_anki_collection_module = ModuleType('anki.collection')
mock_anki_collection_module.Collection = MockCollection
sys.modules['anki.collection'] = mock_anki_collection_module

# Mock anki.utils module
mock_anki_utils_module = ModuleType('anki.utils')
mock_anki_utils_instance = MockAnkiUtils()
mock_anki_utils_module.is_win = mock_anki_utils_instance.is_win
mock_anki_utils_module.isWin = mock_anki_utils_instance.isWin
sys.modules['anki.utils'] = mock_anki_utils_module

# Mock anki.buildinfo module
mock_anki_buildinfo_module = ModuleType('anki.buildinfo')
mock_anki_buildinfo_instance = MockAnkiBuildInfo()
mock_anki_buildinfo_module.version = mock_anki_buildinfo_instance.version
sys.modules['anki.buildinfo'] = mock_anki_buildinfo_module

# Mock anki module (as a package)
mock_anki_module = ModuleType('anki')
mock_anki_module.__path__ = []
mock_anki_module.hooks = mock_anki_hooks_module
mock_anki_module.collection = mock_anki_collection_module
mock_anki_module.utils = mock_anki_utils_module
mock_anki_module.buildinfo = mock_anki_buildinfo_module
sys.modules['anki'] = mock_anki_module

if args.selftest:
    # Set up environment for self-tests (potentially headless)
    is_headless_selftest = os.environ.get('ANKIMON_HEADLESS_SELFTEST', 'False') == 'True'
    mw_instance, dialogs_manager, mock_aqt_gui_hooks_module = setup_test_environment(is_headless_selftest)
    
    if run_self_tests(app, is_headless_selftest):
        logging.info("Self-tests completed successfully. Exiting.")
        sys.exit(0)
    else:
        logging.error("Self-tests failed. Exiting with error.")
        sys.exit(1)

# If not running self-tests, set up the environment based on other args
mw_instance, dialogs_manager, mock_aqt_gui_hooks_module = setup_test_environment(is_headless_file_mode)

if args.file:
    # Individual file testing environment
    file_path = os.path.abspath(args.file)
    if not os.path.exists(file_path):
        logging.error(f"Error: File not found at {file_path}")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("test_module", file_path)
    test_module = importlib.util.module_from_spec(spec)
    sys.modules["test_module"] = test_module
    spec.loader.exec_module(test_module)

    # Look for QDialog or QWidget instances to display
    displayed_widget = None
    for name in dir(test_module):
        obj = getattr(test_module, name)
        if isinstance(obj, (QDialog, QWidget)):
            if hasattr(obj, 'show'):
                obj.show()
                displayed_widget = obj
                break
    else:
        logging.info(f"No QDialog or QWidget found to display in {file_path}")

    if app and hasattr(app, 'processEvents'):
        app.processEvents() # Process any pending events

    if app and hasattr(app, 'quit'):
        app.quit() # Signal the application to exit
    sys.exit(0) # Exit with success code

elif args.full_anki:
    if not app or not isinstance(app, QApplication):
        logging.error("Cannot run full Anki-like interface without a graphical environment (PyQt6 QApplication).")
        sys.exit(1)

    # Enhanced Full Anki-like interface
    logging.info("Starting enhanced Ankimon test environment...")

    # Import the Ankimon addon's components
    try:
        import Ankimon
        logging.info("Ankimon module imported successfully")
    except Exception as e:
        logging.warning(f"Could not import Ankimon module: {e}")

    # Import required components for create_menu_actions
    try:
        from Ankimon.menu_buttons import create_menu_actions, initialize_ankimon_menu
        from Ankimon.pyobj.settings import Settings
        from Ankimon.pyobj.translator import Translator
        from Ankimon.pyobj.InfoLogger import ShowInfoLogger
        from Ankimon.pyobj.collection_dialog import PokemonCollectionDialog
        from Ankimon.pyobj.item_window import ItemWindow
        from Ankimon.pyobj.pc_box import PokemonPC
        logging.info("Ankimon components imported successfully")
    except Exception as e:
        logging.error(f"Could not import Ankimon components: {e}")
        logging.info("Continuing with basic menu setup...")

    # Instantiate required objects for create_menu_actions
    settings_obj = Settings()
    translator_obj = Translator(language=int(settings_obj.get("misc.language", 9)))
    logger_obj = ShowInfoLogger()

    # Initialize Ankimon menu
    pokemenu, game_menu, profile_menu, collection_menu, export_menu, help_menu, debug_menu = initialize_ankimon_menu()

    # Enhanced reviewer object that uses our enhanced MockReviewerWindow
    test_window_obj = MockTestWindow()
    main_pokemon_obj = MockPokemonObject()
    enemy_pokemon_obj = MockEnemyPokemon()
    achievements_obj = MockAchievements()
    starter_window_obj = MockStarterWindow()
    evo_window_obj = MockEvoWindow()
    ankimon_tracker_obj = MockAnkimonTrackerWindow(mw_instance)
    reviewer_obj = MockReviewerManager(settings_obj, main_pokemon_obj, enemy_pokemon_obj, ankimon_tracker_obj)

    # Create a dummy itembag.json file
    temp_dir = Path(tempfile.gettempdir()) # Use Path object for consistency
    itembag_path = temp_dir / "itembag.json"
    with open(itembag_path, "w") as f:
        json.dump([], f)

    # Create dialog objects
    try:
        collection_dialog_obj = PokemonCollectionDialog(
            logger=logger_obj,
            translator=translator_obj,
            reviewer_obj=reviewer_obj,
            test_window=test_window_obj,
            settings_obj=settings_obj,
            main_pokemon=main_pokemon_obj,
            parent=mw_instance
        )

        item_window_obj = ItemWindow(
            logger=logger_obj,
            main_pokemon=main_pokemon_obj,
            enemy_pokemon=enemy_pokemon_obj,
            itembagpath=str(itembag_path), # ItemWindow expects string path
            achievements=achievements_obj,
            starter_window=starter_window_obj,
            evo_window=evo_window_obj,
        )

        pokemon_pc_obj = PokemonPC(
            logger=logger_obj,
            translator=translator_obj,
            reviewer_obj=reviewer_obj,
            test_window=test_window_obj,
            settings=settings_obj,
            main_pokemon=main_pokemon_obj,
            parent=mw_instance
        )
        logging.info("Ankimon dialog objects created successfully")
    except Exception as e:
        logging.warning(f"Could not create some dialog objects: {e}. Using fallback mocks.")
        # Create fallback mock objects
        collection_dialog_obj = MockDialog("PokemonCollection")
        item_window_obj = MockDialog("ItemWindow")
        pokemon_pc_obj = MockDialog("PokemonPC")

    # Create remaining objects
    achievement_window_obj = MockAchievementWindow()
    trainer_card_obj = MockTrainerCard(
        logger=logger_obj,
        main_pokemon=main_pokemon_obj,
        settings_obj=settings_obj,
        trainer_name="MockTrainer",
        badge_count=0,
        trainer_id=123,
    )
    ankimon_tracker_window_obj = MockAnkimonTrackerWindow(mw_instance)
    data_handler_window_obj = MockDataHandlerWindow(mw_instance)
    settings_window_obj = MockSettingsWindow(mw_instance)
    shop_manager_obj = MockPokemonShopManager(mw_instance)
    pokedex_window_obj = MockPokedex(mw_instance)

    # Mock callable functions
    def mock_open_team_builder(): logging.debug("Mock open_team_builder called")
    def mock_export_to_pkmn_showdown(): logging.debug("Mock export_to_pkmn_showdown called")
    def mock_export_all_pkmn_showdown(): logging.debug("Mock export_all_pkmn_showdown called")
    def mock_flex_pokemon_collection(): logging.debug("Mock flex_pokemon_collection called")
    def mock_open_help_window(online_connectivity): logging.debug(f"Mock open_help_window called with {online_connectivity}")
    def mock_report_bug(): logging.debug("Mock report_bug called")
    def mock_rate_addon_url(): logging.debug("Mock rate_addon_url called")
    def mock_join_discord_url(): logging.debug("Mock join_discord_url called")
    def mock_open_leaderboard_url(): logging.debug("Mock open_leaderboard_url called")

    # Create additional mock objects
    eff_chart_obj = MockTableWidget(mw_instance)
    gen_id_chart_obj = MockIDTableWidget(mw_instance)
    credits_obj = MockCredits(mw_instance)
    license_obj = MockLicense(mw_instance)
    version_dialog_obj = MockVersionDialog(mw_instance)
    data_handler_obj = MockDataHandler()

    # Call create_menu_actions to set up the Ankimon menu
    try:
        create_menu_actions(
            database_complete=True,
            online_connectivity=True,
            pokecollection_win=collection_dialog_obj,
            item_window=item_window_obj,
            test_window=test_window_obj,
            achievement_bag=achievement_window_obj,
            open_team_builder=mock_open_team_builder,
            export_to_pkmn_showdown=mock_export_to_pkmn_showdown,
            export_all_pkmn_showdown=mock_export_all_pkmn_showdown,
            flex_pokemon_collection=mock_flex_pokemon_collection,
            eff_chart=eff_chart_obj,
            gen_id_chart=gen_id_chart_obj,
            credits=credits_obj,
            license=license_obj,
            open_help_window=mock_open_help_window,
            report_bug=mock_report_bug,
            rate_addon_url=mock_rate_addon_url,
            version_dialog=version_dialog_obj,
            trainer_card=trainer_card_obj,
            ankimon_tracker_window=ankimon_tracker_window_obj,
            logger=logger_obj,
            data_handler_window=data_handler_window_obj,
            settings_window=settings_window_obj,
            shop_manager=shop_manager_obj,
            pokedex_window=pokedex_window_obj,
            ankimon_key="Ctrl+N",
            join_discord_url=mock_join_discord_url,
            open_leaderboard_url=mock_open_leaderboard_url,
            settings_obj=settings_obj,
            addon_dir=Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'Ankimon'))),
            data_handler_obj=data_handler_obj,
            pokemon_pc=pokemon_pc_obj,
            pokemenu=pokemenu,
            game_menu=game_menu,
            profile_menu=profile_menu,
            collection_menu=collection_menu,
            export_menu=export_menu,
            help_menu=help_menu,
            debug_menu=debug_menu,
        )
        logging.info("Ankimon menu actions created successfully")
    except Exception as e:
        logging.warning(f"Could not create menu actions: {e}")

    # Add enhanced menu items
    # Separator
    if hasattr(mw_instance.pokemenu, 'addSeparator'): mw_instance.pokemenu.addSeparator()

    # Enhanced Reviewer action
    if hasattr(QAction, '__init__'):
        enhanced_reviewer_action = QAction("🎮 Open Enhanced Mock Reviewer", mw_instance)
        enhanced_reviewer_action.triggered.connect(lambda: mw_instance.reviewer_window.show())
        if hasattr(mw_instance.pokemenu, 'addAction'): mw_instance.pokemenu.addAction(enhanced_reviewer_action)

    # Test Hooks action
    if hasattr(QAction, '__init__'):
        test_hooks_action = QAction("🔧 Test Ankimon Hooks", mw_instance)
        def test_hooks():
            logging.debug("Testing Ankimon hooks...")
            # Simulate some hooks
            test_card = MockCard(999, "Test Question", "Test Answer")

            # Test show question hook
            if mock_aqt_gui_hooks_module:
                for func in mock_aqt_gui_hooks_module.reviewer_did_show_question:
                    try:
                        func(test_card)
                    except Exception as e:
                        logging.debug(f"Error in reviewer_did_show_question: {e}")

            # Test answer card hook
            if mock_aqt_gui_hooks_module:
                for func in mock_aqt_gui_hooks_module.reviewer_did_answer_card:
                    try:
                        func(None, test_card, 3)  # Good answer
                    except Exception as e:
                        logging.debug(f"Error in reviewer_did_answer_card: {e}")

            logging.debug("Hook testing completed")

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
            
            info = f"""Enhanced Ankimon Test Environment Debug Info:

Mocked Modules: {num_mocked_modules}
Active Hooks:
- reviewer_did_show_question: {num_q_hooks}
- reviewer_did_show_answer: {num_a_hooks}
- reviewer_did_answer_card: {num_ans_hooks}

Reviewer Status: {reviewer_status}
Cards Available: {cards_available}
            """
            mw_instance.message_box(info)

        debug_info_action.triggered.connect(show_debug_info)
        if hasattr(mw_instance.pokemenu, 'addAction'): mw_instance.pokemenu.addAction(debug_info_action)

    logging.info("Enhanced test environment setup complete!")
    logging.info("Available actions:")
    logging.info("  - Enhanced Mock Reviewer: Full-featured card review simulation")
    logging.info("  - Test Ankimon Hooks: Trigger Ankimon's hook functions")
    logging.info("  - Debug Info: Show current environment status")
    logging.info("  - Various Ankimon menu items (depending on successful imports)")

    # Show the mock main window
    if hasattr(mw_instance, 'show'): mw_instance.show()

    # Start the Qt event loop
    if hasattr(app, 'exec'):
        sys.exit(app.exec())
    else:
        logging.warning("Cannot start Qt event loop in headless mode.")
        sys.exit(0) # Exit gracefully in headless mode if exec not available

else:
    logging.info("Enhanced Ankimon Test Environment")
    logging.info("Usage:")
    logging.info("  --file <path>     Test an individual Python file")
    logging.info("  --full-anki       Run full Anki-like interface with enhanced features")
    logging.info("  --debug           Enable debug logging")
    logging.info("  --selftest        Run self-tests and exit")
    sys.exit(1)
