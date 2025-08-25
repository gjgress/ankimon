import sys
import os
import argparse
import json
import tempfile
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox, QDialog, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QLineEdit, QSizePolicy, QGridLayout, QFrame, QToolTip, QMenuBar, QMenu, QCheckBox
from PyQt6.QtGui import QFont, QPixmap, QImage, QPainter, QFontDatabase, QAction
from PyQt6.QtCore import Qt, QSize, QFile, QUrl, QTimer
from PyQt6.QtWebEngineWidgets import QWebEngineView
from types import ModuleType
import importlib.util

# Helper to load JSON data from Ankimon's user_files
def load_ankimon_json(file_name):
    base_path = Path(__file__).parent.parent / "src" / "Ankimon" / "user_files"
    file_path = base_path / file_name
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARNING] JSON file not found: {file_path}")
        return {}
    except json.JSONDecodeError:
        print(f"[WARNING] Error decoding JSON from file: {file_path}")
        return {}

# Helper to load Ankimon's config.json
def load_ankimon_config():
    config_path = Path(__file__).parent.parent / "src" / "Ankimon" / "config.json"
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARNING] Ankimon config.json not found: {config_path}")
        return {}
    except json.JSONDecodeError:
        print(f"[WARNING] Error decoding JSON from Ankimon config.json: {config_path}")
        return {}

class MockAddonManager:
    def __init__(self):
        self._config = load_ankimon_config()
        self.addonsFolder = Path(__file__).parent.parent / "src" / "Ankimon" # Mock addonsFolder

    def getConfig(self, name):
        return self._config

    def writeConfig(self, name, config):
        print(f"[DEBUG] writeConfig called for {name}")
        # In a real scenario, you might want to write this to a temporary file
        # or update the in-memory config for subsequent getConfig calls.
        self._config.update(config)

    def setWebExports(self, name, pattern):
        print(f"[DEBUG] setWebExports called: {name}, {pattern}")

    def addonFromModule(self, name):
        return "Ankimon"


# Mock Card class to simulate Anki cards
class MockCard:
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

# Enhanced MockReviewerWindow with QWebEngineView and card simulation
class MockReviewerWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Mock Anki Reviewer")
        self.setGeometry(200, 200, 800, 600)
        self.layout = QVBoxLayout(self)

        # Use QWebEngineView for HTML content rendering
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
            btn.hide()
        self.show_answer_btn.show()

    def show_answer_buttons(self):
        """Show answer buttons and hide 'Show Answer' button"""
        for btn in [self.again_btn, self.hard_btn, self.good_btn, self.easy_btn]:
            btn.show()
        self.show_answer_btn.hide()

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

            self.web.setHtml(html_content)
            self.hide_answer_buttons()

            # Trigger reviewer_did_show_question hook
            print(f"[DEBUG] Triggering reviewer_did_show_question for card {card.id}")
            for func in mock_aqt_gui_hooks_module.reviewer_did_show_question:
                try:
                    func(card)
                except Exception as e:
                    print(f"[DEBUG] Error in reviewer_did_show_question hook: {e}")

        else:
            # No more cards
            self.web.setHtml("<div class='card'><h2>No more cards!</h2><p>Review session complete.</p></div>")
            self.hide_answer_buttons()
            self.show_answer_btn.hide()

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

            self.web.setHtml(html_content)
            self.show_answer_buttons()

            # Trigger reviewer_did_show_answer hook
            print(f"[DEBUG] Triggering reviewer_did_show_answer for card {card.id}")
            for func in mock_aqt_gui_hooks_module.reviewer_did_show_answer:
                try:
                    func(card)
                except Exception as e:
                    print(f"[DEBUG] Error in reviewer_did_show_answer hook: {e}")

    def answer_card(self, ease):
        """Answer the current card with the given ease"""
        if hasattr(self, 'current_card'):
            card = self.current_card
            print(f"[DEBUG] Card {card.id} answered with ease: {ease}")

            # Trigger reviewer_did_answer_card hook
            for func in mock_aqt_gui_hooks_module.reviewer_did_answer_card:
                try:
                    func(None, card, ease)  # Pass reviewer, card, ease
                except Exception as e:
                    print(f"[DEBUG] Error in reviewer_did_answer_card hook: {e}")

            # Move to next card
            self.current_card_index += 1

            # Small delay before loading next card for visual feedback
            QTimer.singleShot(300, self.load_current_card)

# Create mock objects
class MockCollection:
    def __init__(self):
        pass

class MockAnkiHooks:
    def addHook(self, *args, **kwargs):
        pass
    def wrap(self, *args, **kwargs):
        def decorator(func):
            return func
        return decorator

class MockGuiHooks:
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
        print(f"[DEBUG] showWarning called: {args}")
    def showInfo(self, *args, **kwargs):
        print(f"[DEBUG] showInfo called: {args}")
    def tr(self, *args, **kwargs):
        return args[0] if args else ""
    def tooltip(self, *args, **kwargs):
        print(f"[DEBUG] tooltip called: {args}")
    def qconnect(self, *args, **kwargs):
        print(f"[DEBUG] qconnect called: {args}")
    def QWebEngineSettings(self, *args, **kwargs):
        return MockQWebEngineSettings()
    def QWebEnginePage(self, *args, **kwargs):
        return MockQWebEnginePage()
    def QWebEngineView(self, *args, **kwargs):
        return QWebEngineView()

# Enhanced MockReviewer that integrates with MockReviewerWindow
class MockQWebEnginePage:
    def __init__(self):
        pass
    def eval(self, js_code):
        print(f"[DEBUG] MockQWebEnginePage.eval called with: {js_code[:100]}...") # Print first 100 chars of JS

class MockQWebEngineView:
    def __init__(self):
        self._page = MockQWebEnginePage()
    def page(self):
        return self._page
    def setHtml(self, html_content):
        print(f"[DEBUG] MockQWebEngineView.setHtml called with: {html_content[:100]}...") # Print first 100 chars of HTML
    def setMinimumHeight(self, height):
        pass # No-op for mock

# Enhanced MockReviewer that integrates with MockReviewerWindow
class MockReviewer:
    _shortcutKeys = {}
    _linkHandler = lambda self, url, _old: True

    def __init__(self):
        self.web = MockQWebEngineView()  # Add web attribute
        self.reviewer_window = None  # Will be set later
        self.card = None  # Current card

    def show(self):
        """Show the reviewer window"""
        print("MockReviewer: show() called.")
        if self.reviewer_window:
            self.reviewer_window.show()

    def setCard(self, card):
        """Set the current card"""
        self.card = card
        print(f"[DEBUG] MockReviewer.setCard called with card: {card}")

    def showQuestion(self):
        print("MockReviewer: showQuestion() called.")
        if self.reviewer_window:
            self.reviewer_window.load_current_card() # This will show the question

    def showAnswer(self):
        print("MockReviewer: showAnswer() called.")
        if self.reviewer_window:
            self.reviewer_window.show_answer() # This will show the answer

    def answerCard(self, ease):
        print(f"MockReviewer: answerCard({ease}) called.")
        if self.reviewer_window:
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

class MockAddonManager:
    def __init__(self):
        pass
    def getConfig(self, name):
        # Return realistic Ankimon config
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
        print(f"[DEBUG] writeConfig called for {name}")
    def setWebExports(self, name, pattern):
        print(f"[DEBUG] setWebExports called: {name}, {pattern}")
    def addonFromModule(self, name):
        return "Ankimon"

# Mock aqt.dialogs for handling dialog opening
class MockDialogManager:
    def __init__(self):
        self.dialogs = {}

    def open(self, name, parent, *args, **kwargs):
        print(f"[DEBUG] aqt.dialogs.open called: {name}, parent: {parent}, args: {args}, kwargs: {kwargs}")
        # Return a mock dialog or handle specific dialog types
        return MockDialog(name)

class MockDialog:
    def __init__(self, name):
        self.name = name
        print(f"[DEBUG] MockDialog created: {name}")

    def show(self):
        print(f"[DEBUG] MockDialog.show called: {self.name}")

    def exec(self):
        print(f"[DEBUG] MockDialog.exec called: {self.name}")
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
    def __init__(self):
        super().__init__()
        self.col = MockCollection()
        self.addonManager = MockAddonManager()
        self.pm = MockProfileManager()
        self.form = MockForm()
        self.form.setupUi(self)
        self.app = app # Assign the global QApplication instance
        
        self.form.setupUi(self)
        self.app = app # Assign the global QApplication instance
        
        self.setWindowTitle("Ankimon Test Environment")
        self.setGeometry(100, 100, 800, 600)

        # Create and integrate MockReviewer with MockReviewerWindow
        self.reviewer = MockReviewer()
        self.reviewer_window = MockReviewerWindow(self)
        self.reviewer.reviewer_window = self.reviewer_window

    def message_box(self, text):
        msg = QMessageBox()
        msg.setText(text)
        msg.exec()

# Additional Mock Classes for Ankimon addon
class MockShowInfoLogger:
    def __init__(self):
        pass
    def log(self, *args, **kwargs): 
        print(f"[DEBUG] Logger.log: {args}")
    def log_and_showinfo(self, *args, **kwargs): 
        print(f"[DEBUG] Logger.log_and_showinfo: {args}")
    def toggle_log_window(self):
        print("[DEBUG] Logger.toggle_log_window called")

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
        self.web = MockQWebEngineView() # Use our mock QWebEngineView

    def update_life_bar(self, reviewer, card, ease):
        # This is a simplified mock of the actual update_life_bar logic
        # It focuses on the eval call that was causing the error
        js_code = "if(window.__ankimonHud) window.__ankimonHud.update('mock_html', 'mock_css');"
        reviewer.web.page().eval(js_code)
        print("[DEBUG] MockReviewerManager.update_life_bar called and eval simulated.")

class MockTestWindow(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Mock Ankimon Window")
        self.setGeometry(300, 300, 800, 600)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("This is a mock Ankimon window."))
        self.setLayout(layout)

    def open_dynamic_window(self):
        print("[DEBUG] MockTestWindow.open_dynamic_window called")
        self.show()

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
    def show_window(self): print("[DEBUG] DataHandlerWindow.show_window called")

class MockSettingsWindow:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): print("[DEBUG] SettingsWindow.show_window called")

class MockPokemonShopManager:
    def __init__(self, *args, **kwargs): pass
    def toggle_window(self): print("[DEBUG] PokemonShopManager.toggle_window called")

class MockPokedex(QDialog):
    def __init__(self, *args, **kwargs): 
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Mock Pokedex")
        self.setGeometry(300, 300, 600, 400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("This is a mock Pokedex window."))
        self.setLayout(layout)

    def show(self):
        print("[DEBUG] MockPokedex.show called")
        self.exec()

class MockAchievementWindow:
    def __init__(self):
        pass
    def show_window(self): print("[DEBUG] AchievementWindow.show_window called")

class MockAnkimonTrackerWindow:
    def __init__(self, *args, **kwargs): pass
    def toggle_window(self): print("[DEBUG] AnkimonTrackerWindow.toggle_window called")

class MockLicense:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): print("[DEBUG] License.show_window called")

class MockCredits:
    def __init__(self, *args, **kwargs): pass
    def show_window(self): print("[DEBUG] Credits.show_window called")

class MockTableWidget:
    def __init__(self, *args, **kwargs): pass
    def show_eff_chart(self): print("[DEBUG] TableWidget.show_eff_chart called")

class MockIDTableWidget:
    def __init__(self, *args, **kwargs): pass
    def show_gen_chart(self): print("[DEBUG] IDTableWidget.show_gen_chart called")

class MockVersionDialog:
    def __init__(self, *args, **kwargs): pass
    def open(self): print("[DEBUG] VersionDialog.open called")

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
        print("[DEBUG] StarterWindow.display_fossil_pokemon called")

class MockEvoWindow:
    def __init__(self):
        pass
    def display_pokemon_evo(self, *args, **kwargs): 
        print("[DEBUG] EvoWindow.display_pokemon_evo called")

class MockPokemonPC(QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle("Mock Pokémon PC")
        self.setGeometry(300, 300, 600, 400)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("This is a mock Pokémon PC window."))
        self.setLayout(layout)

    def show(self):
        print("[DEBUG] MockPokemonPC.show called")
        self.exec()

# Initialize the QApplication here, after all classes are defined
app = QApplication(sys.argv)

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
mock_aqt_utils_module.QWebEngineView = QWebEngineView
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
mock_aqt_webview_module.AnkiWebView = QWebEngineView
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

# Create mw_instance and dialogs_manager after all mock modules are defined
mw_instance = MockMainWindow()
dialogs_manager = MockDialogManager()

# Mock aqt.dialogs module - NEW! (Moved after mw_instance and dialogs_manager)
mock_aqt_dialogs_module = ModuleType('aqt.dialogs')
mock_aqt_dialogs_module.open = dialogs_manager.open
sys.modules['aqt.dialogs'] = mock_aqt_dialogs_module

# Mock aqt module (as a package) - NEW! (Moved after mw_instance and dialogs_manager)
mock_aqt_module = ModuleType('aqt')
mock_aqt_module.__path__ = []
mock_aqt_module.mw = mw_instance
mock_aqt_module.gui_hooks = mock_aqt_gui_hooks_module
mock_aqt_module.utils = mock_aqt_utils_module
mock_aqt_module.qt = mock_aqt_qt_module
mock_aqt_module.reviewer = mock_aqt_reviewer_module
mock_aqt_module.webview = mock_aqt_webview_module
mock_aqt_module.sound = mock_aqt_sound_module
mock_aqt_module.theme = mock_aqt_theme_module
mock_aqt_module.dialogs = mock_aqt_dialogs_module  # NEW!
mock_aqt_module.qconnect = MockUtils().qconnect
mock_aqt_module.QDialog = QDialog
mock_aqt_module.QVBoxLayout = QVBoxLayout
mock_aqt_module.QWebEngineView = QWebEngineView
sys.modules['aqt'] = mock_aqt_module

# --- End of proper mocking ---

# Add the Ankimon addon directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

# Parse command-line arguments
parser = argparse.ArgumentParser(description="Enhanced Ankimon Test Environment")
parser.add_argument('--file', type=str, help='Path to an individual Python file to test')
parser.add_argument('--full-anki', action='store_true', help='Run a full Anki-like interface with enhanced Ankimon menu and reviewer')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')
args = parser.parse_args()

# Enable debug logging if requested
if args.debug:
    print("[DEBUG] Debug mode enabled")

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

    # Look for QDialog or QWidget instances to display
    for name in dir(test_module):
        obj = getattr(test_module, name)
        if isinstance(obj, QDialog) or isinstance(obj, QWidget):
            obj.show()
            break
    else:
        print(f"No QDialog or QWidget found to display in {file_path}")

    sys.exit(app.exec())

elif args.full_anki:
    # Enhanced Full Anki-like interface
    print("[INFO] Starting enhanced Ankimon test environment...")

    # Import the Ankimon addon's components
    try:
        import Ankimon
        print("[INFO] Ankimon module imported successfully")
    except Exception as e:
        print(f"[WARNING] Could not import Ankimon module: {e}")

    # Import required components for create_menu_actions
    try:
        from Ankimon.menu_buttons import create_menu_actions, initialize_ankimon_menu
        from Ankimon.pyobj.settings import Settings
        from Ankimon.pyobj.translator import Translator
        from Ankimon.pyobj.InfoLogger import ShowInfoLogger
        from Ankimon.pyobj.collection_dialog import PokemonCollectionDialog
        from Ankimon.pyobj.item_window import ItemWindow
        from Ankimon.pyobj.pc_box import PokemonPC
        print("[INFO] Ankimon components imported successfully")
    except Exception as e:
        print(f"[ERROR] Could not import Ankimon components: {e}")
        print("[INFO] Continuing with basic menu setup...")

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
    temp_dir = tempfile.gettempdir()
    itembag_path = os.path.join(temp_dir, "itembag.json")
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
            itembagpath=itembag_path,
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
        print("[INFO] Ankimon dialog objects created successfully")
    except Exception as e:
        print(f"[WARNING] Could not create some dialog objects: {e}")
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
    def mock_open_team_builder(): print("[DEBUG] Mock open_team_builder called")
    def mock_export_to_pkmn_showdown(): print("[DEBUG] Mock export_to_pkmn_showdown called")
    def mock_export_all_pkmn_showdown(): print("[DEBUG] Mock export_all_pkmn_showdown called")
    def mock_flex_pokemon_collection(): print("[DEBUG] Mock flex_pokemon_collection called")
    def mock_open_help_window(online_connectivity): print(f"[DEBUG] Mock open_help_window called with {online_connectivity}")
    def mock_report_bug(): print("[DEBUG] Mock report_bug called")
    def mock_rate_addon_url(): print("[DEBUG] Mock rate_addon_url called")
    def mock_join_discord_url(): print("[DEBUG] Mock join_discord_url called")
    def mock_open_leaderboard_url(): print("[DEBUG] Mock open_leaderboard_url called")

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
        print("[INFO] Ankimon menu actions created successfully")
    except Exception as e:
        print(f"[WARNING] Could not create menu actions: {e}")

    # Add enhanced menu items
    # Separator
    mw_instance.pokemenu.addSeparator()

    # Enhanced Reviewer action
    enhanced_reviewer_action = QAction("🎮 Open Enhanced Mock Reviewer", mw_instance)
    enhanced_reviewer_action.triggered.connect(lambda: mw_instance.reviewer_window.show())

    mw_instance.pokemenu.addAction(enhanced_reviewer_action)

    # Test Hooks action
    test_hooks_action = QAction("🔧 Test Ankimon Hooks", mw_instance)
    def test_hooks():
        print("[DEBUG] Testing Ankimon hooks...")
        # Simulate some hooks
        test_card = MockCard(999, "Test Question", "Test Answer")

        # Test show question hook
        for func in mock_aqt_gui_hooks_module.reviewer_did_show_question:
            try:
                func(test_card)
            except Exception as e:
                print(f"[DEBUG] Error in reviewer_did_show_question: {e}")

        # Test answer card hook
        for func in mock_aqt_gui_hooks_module.reviewer_did_answer_card:
            try:
                func(None, test_card, 3)  # Good answer
            except Exception as e:
                print(f"[DEBUG] Error in reviewer_did_answer_card: {e}")

        print("[DEBUG] Hook testing completed")

    test_hooks_action.triggered.connect(test_hooks)
    mw_instance.pokemenu.addAction(test_hooks_action)

    # Debug Info action
    debug_info_action = QAction("ℹ️ Show Debug Info", mw_instance)
    def show_debug_info():
        info = f"""Enhanced Ankimon Test Environment Debug Info:

Mocked Modules: {len([m for m in sys.modules.keys() if m.startswith(('aqt', 'anki'))])}
Active Hooks:
- reviewer_did_show_question: {len(mock_aqt_gui_hooks_module.reviewer_did_show_question)}
- reviewer_did_show_answer: {len(mock_aqt_gui_hooks_module.reviewer_did_show_answer)}
- reviewer_did_answer_card: {len(mock_aqt_gui_hooks_module.reviewer_did_answer_card)}

Reviewer Status: {'Active' if hasattr(mw_instance, 'reviewer_window') else 'Inactive'}
Cards Available: {len(mw_instance.reviewer_window.cards) if hasattr(mw_instance, 'reviewer_window') else 'N/A'}
        """
        mw_instance.message_box(info)

    debug_info_action.triggered.connect(show_debug_info)
    mw_instance.pokemenu.addAction(debug_info_action)

    print("[INFO] Enhanced test environment setup complete!")
    print("[INFO] Available actions:")
    print("  - Enhanced Mock Reviewer: Full-featured card review simulation")
    print("  - Test Ankimon Hooks: Trigger Ankimon's hook functions")
    print("  - Debug Info: Show current environment status")
    print("  - Various Ankimon menu items (depending on successful imports)")

    # Show the mock main window
    mw_instance.show()

    # Start the Qt event loop
    sys.exit(app.exec())

else:
    print("Enhanced Ankimon Test Environment")
    print("Usage:")
    print("  --file <path>     Test an individual Python file")
    print("  --full-anki       Run full Anki-like interface with enhanced features")
    print("  --debug           Enable debug logging")
    sys.exit(1)
