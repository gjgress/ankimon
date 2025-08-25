import sys
import os
import argparse
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSizePolicy, QGridLayout, QFrame, QToolTip, QMenuBar, QMenu
from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter, QFontDatabase, QAction # Import QAction
from PyQt6.QtCore import Qt, QSize, QFile, QUrl
from PyQt6.QtWebEngineWidgets import QWebEngineView # Import QWebEngineView
from types import ModuleType
import importlib.util
import json
import tempfile
from pathlib import Path

# Initialize the QApplication first
app = QApplication(sys.argv)

# --- Crucial: Remove existing Anki/Aqt modules from sys.modules ---
# This ensures our mocks are used instead of any pre-loaded real modules
for module_name in ['aqt', 'anki', 'aqt.qt', 'aqt.reviewer', 'aqt.utils', 'aqt.gui_hooks', 'aqt.webview', 'aqt.sound', 'aqt.theme', 'anki.hooks', 'anki.collection', 'anki.utils', 'anki.buildinfo']:
    if module_name in sys.modules:
        del sys.modules[module_name]

# Create mock objects
class MockCollection:
    def __init__(self):
        pass
    # Add more mock methods/attributes as needed

class MockAnkiHooks:
    def addHook(self, *args, **kwargs):
        pass

    def wrap(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MockGuiHooks:
    def __init__(self):
        self.reviewer_will_end = [] # Mock as a list
        self.reviewer_did_answer_card = [] # Mock as a list
        self.theme_did_change = [] # Mock as a list
        self.reviewer_did_show_question = [] # Mock as a list
        self.reviewer_did_show_answer = [] # Mock as a list
        self.webview_will_set_content = [] # Mock as a list
        self.addon_config_editor_will_display_json = [] # Mock as a list
        self.reviewer_will_answer_card = [] # Mock as a list
        self.profile_did_open = [] # Mock as a list

    def addHook(self, *args, **kwargs):
        pass

class MockQWebEngineSettings:
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
        pass

    def showInfo(self, *args, **kwargs):
        pass

    def tr(self, *args, **kwargs):
        return args[0] if args else ""

    def tooltip(self, *args, **kwargs):
        pass

    def qconnect(self, *args, **kwargs):
        pass

    def QWebEngineSettings(self, *args, **kwargs):
        return MockQWebEngineSettings() # Return an instance of our mock

    def QWebEnginePage(self, *args, **kwargs):
        return MockQWebEnginePage() # Return an instance of our mock

    def QWebEngineView(self, *args, **kwargs):
        return QWebEngineView() # Return an instance of the actual class

class MockReviewer:
    _shortcutKeys = {} # Mock as a dictionary
    _linkHandler = lambda self, url, _old: True # Mock as a function
    def __init__(self):
        pass

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
        self.night_mode = False # Assume light mode by default

class MockAddonManager:
    def __init__(self):
        pass

    def getConfig(self, name):
        # Return the actual config from config.json
        return {
            "battle.dmg_in_reviewer": True,
            "battle.automatic_battle": 0,
            "battle.cards_per_round": 2,
            "battle.daily_average": 100,
            "battle.card_max_time": 60,

            "controls.pokemon_buttons": True,
            "controls.defeat_key": "5",
            "controls.catch_key": "6",
            "controls.key_for_opening_closing_ankimon": "Ctrl+N",
            "controls.allow_to_choose_moves": False,

            "gui.animate_time": True,
            "gui.gif_in_collection": True,
            "gui.styling_in_reviewer": True,
            "gui.hp_bar_config": True,
            "gui.pop_up_dialog_message_on_defeat": False,
            "gui.review_hp_bar_thickness": 2,
            "gui.reviewer_image_gif": False,
            "gui.reviewer_text_message_box": True,
            "gui.reviewer_text_message_box_time": 3,
            "gui.show_mainpkmn_in_reviewer": 1,
            "gui.view_main_front": True,
            "gui.xp_bar_config": True,
            "gui.xp_bar_location": 2,
            
            "audio.sound_effects": False,
            "audio.sounds": True,
            "audio.battle_sounds": False,

            "misc.gen1": True,
            "misc.gen2": True,
            "misc.gen3": True,
            "misc.gen4": True,
            "misc.gen5": True,
            "misc.gen6": True,
            "misc.gen7": False,
            "misc.gen8": False,
            "misc.gen9": False,
            "misc.remove_level_cap": False,
            "misc.leaderboard": False,
            "misc.language": 9,
            "misc.ssh": True,
            "misc.YouShallNotPass_Ankimon_News": False,
            "misc.discord_rich_presence": False,
            "misc.discord_rich_presence_text": 1,
            "misc.show_tip_on_startup": True,
            "misc.last_tip_index": 0,

            "trainer.name": "Ash",
            "trainer.sprite": "ash",
            "trainer.id": 0,
            "trainer.cash": 0
        }

    def writeConfig(self, name, config):
        # For now, just pass. In a real test, you might want to store this.
        pass

    def setWebExports(self, name, pattern):
        # For now, just pass.
        pass

class MockMenuBar(QMenuBar):
    def __init__(self):
        super().__init__()

    def addMenu(self, menu):
        pass

class MockForm:
    def __init__(self):
        self.menubar = MockMenuBar()
        self.centralwidget = QWidget() # Add centralwidget

    def setupUi(self, main_window):
        # This method is typically generated by pyuic and sets up the UI elements
        # For our mock, we just need to ensure the menubar is accessible
        main_window.setMenuBar(self.menubar)
        main_window.setCentralWidget(self.centralwidget)

class MockMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.col = MockCollection()
        self.addonManager = MockAddonManager()
        self.pm = MockProfileManager()
        self.form = MockForm() # Use MockForm here
        self.form.setupUi(self) # Call setupUi
        self.pokemenu = QMenu("Ankimon") # Mock the pokemenu
        self.setWindowTitle("Ankimon Test Environment")
        self.setGeometry(100, 100, 800, 600)

    def message_box(self, text):
        msg = QMessageBox()
        msg.setText(text)
        msg.exec()

# New Mock Classes for create_menu_actions arguments
class MockShowInfoLogger:
    def __init__(self):
        pass
    def log(self, *args, **kwargs): pass
    def log_and_showinfo(self, *args, **kwargs): pass
    def toggle_log_window(self): pass

class MockTranslator:
    def __init__(self, language):
        self.language = language
    def translate(self, key, **kwargs): return f"Translated_{key}"

class MockReviewerManager:
    def __init__(self, *args, **kwargs):
        pass
    def update_life_bar(self, *args, **kwargs): pass

class MockTestWindow:
    def __init__(self, *args, **kwargs):
        pass
    def open_dynamic_window(self): pass
    def isVisible(self): return False
    def display_first_encounter(self): pass

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

    def get_highest_level_pokemon(self): return "None"
    def highest_pokemon_level(self): return 0
    def add_achievement(self, achievement): pass
    def set_team(self, team_pokemons): pass
    def display_card_data(self): return {}
    def xp_for_next_level(self): return 100
    def on_level_up(self): pass
    def gain_xp(self, tier, allow_to_choose_move=False): pass
    def check_level_up(self): pass

class MockDataHandlerWindow:
    def __init__(self, *args, **kwargs):
        pass
    def show_window(self): pass

class MockSettingsWindow:
    def __init__(self, *args, **kwargs):
        pass
    def show_window(self): pass

class MockPokemonShopManager:
    def __init__(self, *args, **kwargs):
        pass
    def toggle_window(self): pass

class MockPokedex:
    def __init__(self, *args, **kwargs):
        pass
    def show(self): pass

class MockAchievementWindow:
    def __init__(self):
        pass
    def show_window(self): pass

class MockAnkimonTrackerWindow:
    def __init__(self, *args, **kwargs):
        pass
    def toggle_window(self): pass

class MockLicense:
    def __init__(self, *args, **kwargs):
        pass
    def show_window(self): pass

class MockCredits:
    def __init__(self, *args, **kwargs):
        pass
    def show_window(self): pass

class MockTableWidget:
    def __init__(self, *args, **kwargs):
        pass
    def show_eff_chart(self): pass

class MockIDTableWidget:
    def __init__(self, *args, **kwargs):
        pass
    def show_gen_chart(self): pass

class MockVersionDialog:
    def __init__(self, *args, **kwargs):
        pass
    def open(self): pass

class MockDataHandler:
    def __init__(self, *args, **kwargs):
        pass

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
    def display_fossil_pokemon(self, *args, **kwargs): pass

class MockEvoWindow:
    def __init__(self):
        pass
    def display_pokemon_evo(self, *args, **kwargs): pass

# Create instances of our mock objects
mw_instance = MockMainWindow()

# --- Proper mocking of anki and aqt modules ---

# Mock aqt.qt module
mock_aqt_qt_module = ModuleType('aqt.qt')
mock_aqt_qt_module.QDialog = QDialog # Expose QDialog
mock_aqt_qt_module.qconnect = MockUtils().qconnect # Expose qconnect
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
mock_aqt_utils_module.QWebEngineSettings = MockQWebEngineSettings # Expose QWebEngineSettings
mock_aqt_utils_module.QWebEnginePage = MockQWebEnginePage # Expose QWebEnginePage
mock_aqt_utils_module.QWebEngineView = QWebEngineView # Expose QWebEngineView
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
mock_aqt_webview_module.AnkiWebView = QWebEngineView # Use actual QWebEngineView
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


# Mock aqt module (as a package)
mock_aqt_module = ModuleType('aqt')
mock_aqt_module.__path__ = [] # Essential to make it a package
mock_aqt_module.mw = mw_instance
mock_aqt_module.gui_hooks = mock_aqt_gui_hooks_module # Attach the gui_hooks submodule
mock_aqt_module.utils = mock_aqt_utils_module # Attach the utils submodule
mock_aqt_module.qt = mock_aqt_qt_module # Attach the qt submodule
mock_aqt_module.reviewer = mock_aqt_reviewer_module # Attach the reviewer submodule
mock_aqt_module.webview = mock_aqt_webview_module # Attach the webview submodule
mock_aqt_module.sound = mock_aqt_sound_module # Attach the sound submodule
mock_aqt_module.theme = mock_aqt_theme_module # Attach the theme submodule
mock_aqt_module.qconnect = MockUtils().qconnect # Re-export qconnect at top level
mock_aqt_module.QDialog = QDialog # Re-export QDialog at top level
mock_aqt_module.QVBoxLayout = QVBoxLayout # Re-export QVBoxLayout at top level
mock_aqt_module.QWebEngineView = QWebEngineView # Use actual QWebEngineView
sys.modules['aqt'] = mock_aqt_module

# Mock anki.hooks module
mock_anki_hooks_module = ModuleType('anki.hooks')
mock_anki_hooks_instance = MockAnkiHooks()
mock_anki_hooks_module.addHook = mock_anki_hooks_instance.addHook
mock_anki_hooks_module.wrap = mock_anki_hooks_instance.wrap
sys.modules['anki.hooks'] = mock_anki_hooks_module

# Mock anki.collection module
mock_anki_collection_module = ModuleType('anki.collection')
mock_anki_collection_module.Collection = MockCollection # Assuming Collection is a class
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
mock_anki_module.__path__ = [] # Essential to make it a package
mock_anki_module.hooks = mock_anki_hooks_module
mock_anki_module.collection = mock_anki_collection_module
mock_anki_module.utils = mock_anki_utils_module # Attach the utils submodule
mock_anki_module.buildinfo = mock_anki_buildinfo_module # Attach the buildinfo submodule
sys.modules['anki'] = mock_anki_module

# --- End of proper mocking ---

# Add the Ankimon addon directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Define MockReviewerWindow

from PyQt6.QtWebEngineWidgets import QWebEngineView

class MockCard:
    """A mock card object for simulating Anki's Card."""
    def __init__(self, qid, did, front, back):
        self.id = qid
        self.did = did
        self.note = MockNote(front, back)
        self.question = front
        self.answer = back

class MockNote:
    """A mock note object for simulating Anki's Note."""
    def __init__(self, front, back):
        self.fields = [front, back]

class MockReviewerWindow(QMainWindow):
    def __init__(self, mw):
        super().__init__()
        self.mw = mw
        self.setWindowTitle("Mock Reviewer Window")
        self.setGeometry(100, 100, 800, 600)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Use QWebEngineView for HTML content
        self.web_view = QWebEngineView()
        self.layout.addWidget(self.web_view)

        self.answer_buttons_layout = QHBoxLayout()
        self.layout.addLayout(self.answer_buttons_layout)

        self.again_btn = QPushButton("Again")
        self.again_btn.clicked.connect(lambda: self._answer_card(1))
        self.answer_buttons_layout.addWidget(self.again_btn)

        self.hard_btn = QPushButton("Hard")
        self.hard_btn.clicked.connect(lambda: self._answer_card(2))
        self.answer_buttons_layout.addWidget(self.hard_btn)

        self.good_btn = QPushButton("Good")
        self.good_btn.clicked.connect(lambda: self._answer_card(3))
        self.answer_buttons_layout.addWidget(self.good_btn)

        self.easy_btn = QPushButton("Easy")
        self.easy_btn.clicked.connect(lambda: self._answer_card(4))
        self.answer_buttons_layout.addWidget(self.easy_btn)

        self.dummy_cards = [
            {"id": 1, "did": 101, "front": "What is the capital of France?", "back": "Paris"},
            {"id": 2, "did": 101, "front": "What is 2 + 2?", "back": "4"},
            {"id": 3, "did": 102, "front": "Who painted the Mona Lisa?", "back": "Leonardo da Vinci"},
            {"id": 4, "did": 102, "front": "HTML stands for?", "back": "HyperText Markup Language"},
        ]
        self.current_card_index = 0
        self.current_mock_card = None

        self.show_next_card()

    def show_next_card(self):
        if not self.dummy_cards:
            self.web_view.setHtml("<h1>No more cards!</h1>")
            return

        card_data = self.dummy_cards[self.current_card_index]
        self.current_mock_card = MockCard(
            card_data["id"], card_data["did"], card_data["front"], card_data["back"]
        )

        # Simulate reviewer_did_show_question
        print(f"MockReviewerWindow: Simulating reviewer_did_show_question for card ID {self.current_mock_card.id}")
        gui_hooks.reviewer_did_show_question(self.current_mock_card)

        self.web_view.setHtml(f"<h2>{card_data['front']}</h2>")

    def _answer_card(self, ease):
        if not self.current_mock_card:
            print("MockReviewerWindow: No current card to answer.")
            return

        print(f"MockReviewerWindow: Answering card ID {self.current_mock_card.id} with ease {ease}")
        # Simulate gui_hooks.reviewer_did_answer_card
        gui_hooks.reviewer_did_answer_card(self, self.current_mock_card, ease)

        # Simulate reviewer_did_show_answer
        print(f"MockReviewerWindow: Simulating reviewer_did_show_answer for card ID {self.current_mock_card.id}")
        gui_hooks.reviewer_did_show_answer(self.current_mock_card)

        # Display the answer
        self.web_view.setHtml(
            f"<h2>{self.current_mock_card.question}</h2><hr><h3>{self.current_mock_card.answer}</h3>"
        )

        # Move to the next card after a short delay to show the answer
        QTimer.singleShot(1500, self._advance_card_and_show_next)

    def _advance_card_and_show_next(self):
        self.current_card_index = (self.current_card_index + 1) % len(self.dummy_cards)
        self.show_next_card()

    def show_card(self, content):
        # This method might be called by Ankimon, so we keep it for compatibility
        print(f"MockReviewerWindow: show_card called with content: {content}")
        self.web_view.setHtml(content)


# Parse command-line arguments
parser = argparse.ArgumentParser(description="Ankimon Test Environment")
parser.add_argument('--file', type=str, help='Path to an individual Python file to test (e.g., src/Ankimon/pyobj/pc_box.py)')
parser.add_argument('--full-anki', action='store_true', help='Run a full Anki-like interface with Ankimon menu and reviewer')
args = parser.parse_args()

if args.file:
    # Individual file testing environment
    file_path = os.path.abspath(args.file)
    if not os.path.exists(file_path):
        print(f"Error: File not found at {file_path}")
        sys.exit(1)

    spec = importlib.util.spec_from_file_location("test_module", file_path)
    test_module = importlib.util.module_from_spec(spec)
    sys.modules["test_module"] = test_module
    spec.loader.exec_module(test_module)

    # Assuming the file might create a QDialog or QWidget, try to show it
    for name in dir(test_module):
        obj = getattr(test_module, name)
        if isinstance(obj, QDialog) or isinstance(obj, QWidget):
            obj.show()
            break
    else:
        print(f"No QDialog or QWidget found to display in {file_path}")

    sys.exit(app.exec())
elif args.full_anki:
    # Full Anki-like interface
    # Import the Ankimon addon's __init__.py
    # This will trigger the addon's initialization and it should use our mock mw
    import Ankimon

    # Call create_menu_actions to set up the Ankimon menu
    from Ankimon.menu_buttons import create_menu_actions
    from Ankimon.pyobj.settings import Settings
    from Ankimon.pyobj.translator import Translator
    from Ankimon.pyobj.InfoLogger import ShowInfoLogger
    from Ankimon.pyobj.collection_dialog import PokemonCollectionDialog
    from Ankimon.pyobj.item_window import ItemWindow
    from Ankimon.pyobj.test_window import TestWindow
    from Ankimon.pyobj.achievement_window import AchievementWindow
    from Ankimon.pyobj.pc_box import PokemonPC
    from Ankimon.pyobj.trainer_card import TrainerCard
    from Ankimon.pyobj.data_handler_window import DataHandlerWindow
    from Ankimon.pyobj.settings_window import SettingsWindow
    from Ankimon.pyobj.ankimon_shop import PokemonShopManager
    from Ankimon.pokedex.pokedex_obj import Pokedex
    from Ankimon.gui_classes.pokemon_team_window import PokemonTeamDialog
    from Ankimon.gui_classes.check_files import FileCheckerApp
    from Ankimon.pyobj.download_sprites import show_agreement_and_download_dialog
    from Ankimon.pyobj.ankimon_leaderboard import show_api_key_dialog
    from Ankimon.pyobj.data_handler import DataHandler
    from Ankimon.gui_classes.choose_trainer_sprite import TrainerSpriteDialog

    # Instantiate required objects for create_menu_actions
    settings_obj = Settings()
    translator_obj = Translator(language=int(settings_obj.get("misc.language", 9)))
    logger_obj = ShowInfoLogger()

    # Mock Reviewer_Manager with a web attribute that has a setHtml method
    class MockReviewerManager:
        def __init__(self, *args, **kwargs):
            self.web = QWebEngineView() # Use actual QWebEngineView
        def update_life_bar(self, *args, **kwargs): pass

    reviewer_obj = MockReviewerManager()

    # Mock TestWindow with a web attribute that has a setHtml method
    class MockTestWindow:
        def __init__(self, *args, **kwargs):
            self.web = QWebEngineView() # Use actual QWebEngineView
        def open_dynamic_window(self): pass
        def isVisible(self): return False
        def display_first_encounter(self): pass

    test_window_obj = MockTestWindow()

    # Mock PokemonObject with a to_dict method and calc_stat static method
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

    main_pokemon_obj = MockPokemonObject()
    enemy_pokemon_obj = MockEnemyPokemon()
    achievements_obj = MockAchievements()
    starter_window_obj = MockStarterWindow()
    evo_window_obj = MockEvoWindow()

    # Create a dummy itembag.json file
    temp_dir = tempfile.gettempdir()
    itembag_path = os.path.join(temp_dir, "itembag.json")
    with open(itembag_path, "w") as f:
        json.dump([], f) # Empty list for now

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
        itembagpath=itembag_path, # Use the path to the dummy file
        achievements=achievements_obj,
        starter_window=starter_window_obj,
        evo_window=evo_window_obj,
    )
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
    pokemon_pc_obj = PokemonPC(
        logger=logger_obj,
        translator=translator_obj,
        reviewer_obj=reviewer_obj,
        test_window=test_window_obj,
        settings=settings_obj,
        main_pokemon=main_pokemon_obj,
        parent=mw_instance
    )

    # Mock Callables
    def mock_open_team_builder(): print("Mock open_team_builder called")
    def mock_export_to_pkmn_showdown(): print("Mock export_to_pkmn_showdown called")
    def mock_export_all_pkmn_showdown(): print("Mock export_all_pkmn_showdown called")
    def mock_flex_pokemon_collection(): print("Mock flex_pokemon_collection called")
    def mock_open_help_window(online_connectivity): print(f"Mock open_help_window called with online_connectivity={online_connectivity}")
    def mock_report_bug(): print("Mock report_bug called")
    def mock_rate_addon_url(): print("Mock rate_addon_url called")
    def mock_join_discord_url(): print("Mock join_discord_url called")
    def mock_open_leaderboard_url(): print("Mock open_leaderboard_url called")

    eff_chart_obj = MockTableWidget(mw_instance)
    gen_id_chart_obj = MockIDTableWidget(mw_instance)
    credits_obj = MockCredits(mw_instance)
    license_obj = MockLicense(mw_instance)
    version_dialog_obj = MockVersionDialog(mw_instance)
    data_handler_obj = MockDataHandler()

    create_menu_actions(
        database_complete=True, # Placeholder, adjust as needed
        online_connectivity=True, # Placeholder, adjust as needed
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
        ankimon_key="Ctrl+N", # Placeholder, adjust as needed
        join_discord_url=mock_join_discord_url,
        open_leaderboard_url=mock_open_leaderboard_url,
        settings_obj=settings_obj,
        addon_dir=Path(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src', 'Ankimon'))),
        data_handler_obj=data_handler_obj,
        pokemon_pc=pokemon_pc_obj,
    )

    # Add a menu item to open the MockReviewerWindow
    reviewer_action = QAction("Open Mock Reviewer", mw_instance)
    reviewer_action.triggered.connect(lambda: MockReviewerWindow(mw_instance).show())
    mw_instance.pokemenu.addAction(reviewer_action)

    # Show the mock main window
    mw_instance.show()

    # Start the Qt event loop
    sys.exit(app.exec())
else:
    print("Please specify either --file <path> or --full-anki")
    sys.exit(1)
