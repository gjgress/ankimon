import sys
import os
import argparse
import logging
import subprocess
import importlib
import threading
from pathlib import Path
import ast # For parsing docstrings
import json # For config editor

# --- PyQt6 Imports ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QTabWidget, QStatusBar, QDialog, QTextEdit, QPushButton,
    QListWidget, QListWidgetItem, QHBoxLayout, QSizePolicy,
    QColorDialog, QFileDialog, QPlainTextEdit, QSplitter
)
from PyQt6.QtCore import Qt, QObject, QSignalMapper, QVariant, QTimer, QThread, pyqtSignal, QCoreApplication
from PyQt6.QtGui import QPalette, QColor, QAction, QIcon, QFont

# --- Mocking Anki Components ---
try:
    from ankimon_test_env.mock_anki import Collection as MockCollection
    from ankimon_test_env.mock_anki import ProfileManager as MockProfileManager
    from ankimon_test_env.mock_anki import Card as MockCard
    from ankimon_test_env.mock_anki import AnkiUtils as MockAnkiUtils
    from ankimon_test_env.mock_anki import BuildInfo as MockBuildInfo
    from ankimon_test_env.mock_anki import DataHandler as MockDataHandler
    from ankimon_test_env.mock_anki import EnemyPokemon as MockEnemyPokemon
    from ankimon_test_env.mock_anki import Achievements as MockAchievements
except ImportError as e:
    print(f"Error importing mock Anki components: {e}")
    print("Please ensure 'ankimon_test_env/mock_anki' is correctly set up.")
    sys.exit(1)

try:
    from ankimon_test_env.mock_aqt import MainWindow as MockMainWindow
    from ankimon_test_env.mock_aqt import Utils as MockUtils
    from ankimon_test_env.mock_aqt import Dialog as MockDialog
    from ankimon_test_env.mock_aqt import AddonManager as MockAddonManager
    from ankimon_test_env.mock_aqt import Collection as MockAqtCollection # Renamed to avoid conflict
    from ankimon_test_env.mock_aqt import Reviewer as MockReviewer
    from ankimon_test_env.mock_aqt import ReviewerWindow as MockReviewerWindow
    from ankimon_test_env.mock_aqt import PokemonObject as MockPokemonObject
    from ankimon_test_env.mock_aqt import TrainerCard as MockTrainerCard
    from ankimon_test_env.mock_aqt import DataHandlerWindow as MockDataHandlerWindow
    from ankimon_test_env.mock_aqt import SettingsWindow as MockSettingsWindow
    from ankimon_test_env.mock_aqt import PokemonShopManager as MockPokemonShopManager
    from ankimon_test_env.mock_aqt import Pokedex as MockPokedex
    from ankimon_test_env.mock_aqt import AchievementWindow as MockAchievementWindow
    from ankimon_test_env.mock_aqt import AnkimonTrackerWindow as MockAnkimonTrackerWindow
    from ankimon_test_env.mock_aqt import License as MockLicense
    from ankimon_test_env.mock_aqt import Credits as MockCredits
    from ankimon_test_env.mock_aqt import TableWidget as MockTableWidget
    from ankimon_test_env.mock_aqt import IDTableWidget as MockIDTableWidget
    from ankimon_test_env.mock_aqt import VersionDialog as MockVersionDialog
    from ankimon_test_env.mock_aqt import StarterWindow as MockStarterWindow
    from ankimon_test_env.mock_aqt import EvoWindow as MockEvoWindow
    from ankimon_test_env.mock_aqt import PokemonPC as MockPokemonPC
    from ankimon_test_env.mock_aqt import QWebEngineSettings as MockQWebEngineSettings
    from ankimon_test_env.mock_aqt import QWebEnginePage as MockQWebEnginePage
    from ankimon_test_env.mock_aqt import WebContent as MockWebContent
    from ankimon_test_env.mock_aqt import SoundOrVideoTag as MockSoundOrVideoTag
    from ankimon_test_env.mock_aqt import AVPlayer as MockAVPlayer
    from ankimon_test_env.mock_aqt import ThemeManager as MockThemeManager
    from ankimon_test_env.mock_aqt import DialogManager as MockDialogManager
    from ankimon_test_env.mock_aqt import Menu as MockMenu
    from ankimon_test_env.mock_aqt import Action as MockAction
    from ankimon_test_env.mock_aqt import Signal as MockSignal
    from ankimon_test_env.mock_aqt import Form as MockForm
    from ankimon_test_env.mock_aqt import ShowInfoLogger as MockShowInfoLogger
    from ankimon_test_env.mock_aqt import Translator as MockTranslator
    from ankimon_test_env.mock_aqt import ReviewerManager as MockReviewerManager
except ImportError as e:
    print(f"Error importing mock aqt components: {e}")
    print("Please ensure 'ankimon_test_env/mock_aqt' is correctly set up.")
    sys.exit(1)

# Import the TestRunnerThread from its own file
try:
    from ankimon_test_env.test_runner import TestRunnerThread
except ImportError:
    print("Error: Could not import TestRunnerThread. Ensure 'ankimon_test_env/test_runner.py' exists.")
    sys.exit(1)

# --- Test Runner Configuration ---
ANKIMON_TESTS_DIR = "ankimon_test_env/tests/"
TEST_FILE_PATTERN = "*.py"

# --- Global Variables ---
mw = None
app = None

# --- Logging Configuration ---
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# --- GUI Components ---

class LogViewerWidget(logging.Handler):
    """A logging handler that writes to a QTextEdit widget."""
    def __init__(self, parent):
        super().__init__()
        self.widget = QTextEdit(parent)
        self.widget.setReadOnly(True)
        self.widget.setPlaceholderText("Ankimon Test Environment Logs...")
        self.widget.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                padding: 5px;
                font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
                font-size: 10pt;
                color: #f0f0f0;
            }
        """)

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)

class TestBrowserWidget(QWidget):
    """Widget for browsing and running tests."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.test_threads = {}
        self.current_test_item = None # To track the currently running test item

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("<h2>Test Browser</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Test Directory Label
        dir_label = QLabel(f"<b>Test Directory:</b> {os.path.abspath(ANKIMON_TESTS_DIR)}")
        dir_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(dir_label)

        # Splitter for List/Output
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: #555555; }")

        # Top pane: Test List and Controls
        top_pane_widget = QWidget()
        top_layout = QVBoxLayout(top_pane_widget)

        self.test_list_widget = QListWidget()
        self.test_list_widget.setAlternatingRowColors(True)
        self.test_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                padding: 5px;
                font-size: 10pt;
                color: #f0f0f0;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #3c3c3c;
            }
            QListWidget::item:selected {
                background-color: #2a82da;
                color: #ffffff;
            }
            QListWidget::item:hover {
                background-color: #3c3c3c;
            }
        """)
        top_layout.addWidget(self.test_list_widget)

        # Buttons for Test Actions
        button_layout = QHBoxLayout()
        self.discover_button = QPushButton("Discover Tests")
        self.discover_button.clicked.connect(self.discover_tests)
        self.run_all_button = QPushButton("Run All")
        self.run_all_button.clicked.connect(self.run_all_tests)
        self.stop_all_button = QPushButton("Stop All")
        self.stop_all_button.clicked.connect(self.stop_all_tests)
        self.stop_all_button.setEnabled(False)

        button_layout.addWidget(self.discover_button)
        button_layout.addWidget(self.run_all_button)
        button_layout.addWidget(self.stop_all_button)
        top_layout.addLayout(button_layout)

        splitter.addWidget(top_pane_widget)

        # Bottom pane: Output Area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("Test execution output will appear here...")
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                padding: 5px;
                font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
                font-size: 10pt;
                color: #f0f0f0;
            }
        """)
        self.output_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.addWidget(self.output_area)

        layout.addWidget(splitter)

        # Status Label
        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.status_label)

        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; }
            QLabel { color: #f0f0f0; }
        """)

        # Initial discovery on load
        self.discover_tests()

    def discover_tests(self):
        """Discovers .py files in the ANKIMON_TESTS_DIR."""
        self.test_list_widget.clear()
        self.output_area.clear()
        self.status_label.setText("Status: Discovering tests...")
        self.parent_window.status_bar.showMessage("Discovering tests...")

        tests_found = False
        try:
            tests_path = Path(ANKIMON_TESTS_DIR)
            if not tests_path.is_dir():
                self.output_area.append(f"Error: Test directory not found: {ANKIMON_TESTS_DIR}")
                self.status_label.setText("Status: Test directory not found.")
                return

            for test_file in tests_path.glob(TEST_FILE_PATTERN):
                if test_file.is_file():
                    item = QListWidgetItem(test_file.name)
                    item.setData(Qt.ItemDataRole.UserRole, str(test_file.resolve())) # Store full path
                    self.test_list_widget.addItem(item)
                    tests_found = True

            if not tests_found:
                item = QListWidgetItem("No tests found in ankimon_test_env/tests/")
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable)
                self.test_list_widget.addItem(item)
                self.status_label.setText("Status: No tests found.")
            else:
                self.status_label.setText(f"Status: Found {self.test_list_widget.count()} tests.")
                self.parent_window.status_bar.showMessage(f"Found {self.test_list_widget.count()} tests.")

        except Exception as e:
            error_msg = f"Error during test discovery: {e}"
            self.output_area.append(error_msg)
            self.status_label.setText("Status: Error during discovery.")
            self.parent_window.status_bar.showMessage("Error during test discovery.")
            logger.error(error_msg)

    def run_test(self, item):
        """Starts a test in a separate thread."""
        test_file_path = item.data(Qt.ItemDataRole.UserRole)
        test_name = item.text().split(" (")[0] # Remove status suffix

        if not test_file_path or "No tests found" in test_name:
            self.output_area.append("Cannot run this item.")
            return

        if test_file_path in self.test_threads and self.test_threads[test_file_path].isRunning():
            self.output_area.append(f"Test '{test_name}' is already running.")
            return

        # Reset previous item's status if it was running
        if self.current_test_item and self.current_test_item != item:
            self.reset_item_status(self.current_test_item)

        self.current_test_item = item
        thread = TestRunnerThread(test_file_path, test_name)
        thread.output_signal.connect(self.append_output)
        thread.finished_signal.connect(self.handle_test_finish)
        self.test_threads[test_file_path] = thread
        thread.start()

        self.status_label.setText(f"Status: Running '{test_name}'...")
        self.parent_window.status_bar.showMessage(f"Running '{test_name}'...")
        self.run_all_button.setEnabled(False)
        self.discover_button.setEnabled(False)
        self.stop_all_button.setEnabled(True)

    def run_all_tests(self):
        """Runs all discovered tests sequentially."""
        if self.test_list_widget.count() == 0:
            self.output_area.append("No tests to run. Please discover tests first.")
            return

        self.output_area.clear()
        self.status_label.setText("Status: Starting all tests...")
        self.parent_window.status_bar.showMessage("Starting all tests...")
        self.run_all_button.setEnabled(False)
        self.discover_button.setEnabled(False)
        self.stop_all_button.setEnabled(True)

        for i in range(self.test_list_widget.count()):
            item = self.test_list_widget.item(i)
            test_name = item.text().split(" (")[0]
            if "No tests found" in test_name:
                continue

            # Reset item status before running
            self.reset_item_status(item)
            self.current_test_item = item # Set current item for this iteration

            self.run_test(item)
            if item.data(Qt.ItemDataRole.UserRole) in self.test_threads:
                self.test_threads[item.data(Qt.ItemDataRole.UserRole)].wait() # Wait for this thread to complete

        self.status_label.setText("Status: All tests finished.")
        self.parent_window.status_bar.showMessage("All tests finished.")
        self.run_all_button.setEnabled(True)
        self.discover_button.setEnabled(True)
        self.stop_all_button.setEnabled(False)

    def stop_all_tests(self):
        """Stops all currently running tests."""
        self.status_label.setText("Status: Stopping tests...")
        self.parent_window.status_bar.showMessage("Stopping tests...")
        for test_file_path, thread in self.test_threads.items():
            if thread.isRunning():
                thread.stop()
                thread.wait()
        self.test_threads.clear()
        self.current_test_item = None
        self.status_label.setText("Status: All tests stopped.")
        self.parent_window.status_bar.showMessage("All tests stopped.")
        self.run_all_button.setEnabled(True)
        self.discover_button.setEnabled(True)
        self.stop_all_button.setEnabled(False)

    def append_output(self, text):
        """Appends text to the output area."""
        self.output_area.insertPlainText(text)
        self.output_area.ensureCursorVisible()

    def reset_item_status(self, item):
        """Resets the visual status of a list item."""
        original_text = item.text().split(" (")[0]
        item.setText(original_text)
        item.setForeground(QColor("black")) # Reset color

    def handle_test_finish(self, test_name, success, docstring):
        """Updates UI when a test finishes."""
        for i in range(self.test_list_widget.count()):
            item = self.test_list_widget.item(i)
            if item.text().split(" (")[0] == test_name:
                if success:
                    item.setForeground(QColor("green"))
                    item.setText(f"{test_name} (PASSED)")
                else:
                    item.setForeground(QColor("red"))
                    item.setText(f"{test_name} (FAILED)")
                # Store docstring with the item for later display
                item.setData(Qt.ItemDataRole.UserRole + 1, docstring)
                break

        # Check if all tests are done to re-enable buttons
        all_tests_finished = True
        for test_file_path, thread in self.test_threads.items():
            if thread.isRunning():
                all_tests_finished = False
                break

        if all_tests_finished:
            self.status_label.setText("Status: All tests finished.")
            self.parent_window.status_bar.showMessage("All tests finished.")
            self.run_all_button.setEnabled(True)
            self.discover_button.setEnabled(True)
            self.stop_all_button.setEnabled(False)
        else:
            self.status_label.setText(f"Status: Test '{test_name}' finished. More tests running...")
            self.parent_window.status_bar.showMessage(f"Test '{test_name}' finished. More tests running...")

        # Connect itemClicked to display docstring/output
        self.test_list_widget.itemClicked.connect(self.display_test_details)

    def display_test_details(self, item):
        """Displays the docstring and output for a selected test."""
        test_name = item.text().split(" (")[0]
        docstring = item.data(Qt.ItemDataRole.UserRole + 1)
        if docstring:
            self.output_area.setPlainText(f"--- Details for: {test_name} ---\n\n{docstring}\n\n--- Output ---\n")
            # Append actual output if available (this requires storing output per test)
            # For now, we'll just show the docstring.
            # A more advanced approach would store output in a dict keyed by test name.
        else:
            self.output_area.setPlainText(f"--- Details for: {test_name} ---\n\nNo docstring available.\n\n--- Output ---\n")


class ReviewerSimulationWidget(QWidget):
    """Widget for simulating the Ankimon reviewer workflow."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.current_card_index = 0
        self.mock_cards = [] # List to hold mock card data
        self.session_actions = [] # To log actions taken

        layout = QVBoxLayout(self)

        title_label = QLabel("<h2>Simulated Reviewer</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Card display area
        self.card_display = QWidget()
        self.card_layout = QVBoxLayout(self.card_display)
        self.card_display.setStyleSheet("""
            QWidget { background-color: #2d2d2d; border: 1px solid #555555; border-radius: 5px; padding: 10px; }
            QLabel { color: #f0f0f0; font-size: 12pt; }
            QPushButton { background-color: #555555; color: white; padding: 8px 15px; border-radius: 4px; }
            QPushButton:hover { background-color: #666666; }
        """)
        self.question_label = QLabel("Question: Loading...")
        self.question_label.setWordWrap(True)
        self.answer_label = QLabel("Answer: Loading...")
        self.answer_label.setWordWrap(True)
        self.answer_label.hide() # Initially hidden

        self.card_layout.addWidget(self.question_label)
        self.card_layout.addWidget(self.answer_label)
        layout.addWidget(self.card_display)

        # Ease buttons
        ease_layout = QHBoxLayout()
        self.again_button = QPushButton("Again")
        self.hard_button = QPushButton("Hard")
        self.good_button = QPushButton("Good")
        self.easy_button = QPushButton("Easy")

        self.again_button.clicked.connect(lambda: self.handle_ease_selection("Again"))
        self.hard_button.clicked.connect(lambda: self.handle_ease_selection("Hard"))
        self.good_button.clicked.connect(lambda: self.handle_ease_selection("Good"))
        self.easy_button.clicked.connect(lambda: self.handle_ease_selection("Easy"))

        ease_layout.addWidget(self.again_button)
        ease_layout.addWidget(self.hard_button)
        ease_layout.addWidget(self.good_button)
        ease_layout.addWidget(self.easy_button)
        layout.addLayout(ease_layout)

        # Hooks and Actions Log
        self.hooks_log_label = QLabel("Hooks Log:")
        self.hooks_log_display = QTextEdit()
        self.hooks_log_display.setReadOnly(True)
        self.hooks_log_display.setFixedHeight(100)
        self.hooks_log_display.setStyleSheet("""
            QTextEdit {
                background-color: #2d2d2d; border: 1px solid #555555; padding: 5px; font-size: 9pt; color: #f0f0f0;
            }
        """)
        layout.addWidget(self.hooks_log_label)
        layout.addWidget(self.hooks_log_display)

        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; }
            QLabel { color: #f0f0f0; }
        """)

        # Initialize with some mock cards
        self.load_mock_cards()
        self.display_card()

    def load_mock_cards(self):
        """Loads some sample mock cards."""
        self.mock_cards = [
            {"id": 1, "question": "What is the capital of France?", "answer": "Paris", "ease": "Good"},
            {"id": 2, "question": "What is 2 + 2?", "answer": "4", "ease": "Easy"},
            {"id": 3, "question": "Who wrote Hamlet?", "answer": "William Shakespeare", "ease": "Hard"},
            {"id": 4, "question": "What is the chemical symbol for water?", "answer": "H2O", "ease": "Again"},
        ]
        self.current_card_index = 0
        self.session_actions = []

    def display_card(self):
        """Displays the current card's question."""
        if not self.mock_cards:
            self.question_label.setText("No cards available.")
            self.answer_label.hide()
            self.hide_ease_buttons()
            return

        card = self.mock_cards[self.current_card_index]
        self.question_label.setText(f"Q: {card['question']}")
        self.answer_label.setText(f"A: {card['answer']}")
        self.answer_label.hide() # Hide answer until revealed
        self.show_ease_buttons()
        self.log_action(f"Displayed card {card['id']}: {card['question']}")

    def reveal_answer(self):
        """Reveals the answer to the current card."""
        self.answer_label.show()
        self.log_action(f"Revealed answer for card {self.mock_cards[self.current_card_index]['id']}")

    def handle_ease_selection(self, ease):
        """Handles user selection of ease buttons."""
        if not self.mock_cards:
            return

        card = self.mock_cards[self.current_card_index]
        self.log_action(f"Selected '{ease}' for card {card['id']} (Answer: {card['answer']})")

        # Simulate hook invocation (e.g., for Ankimon's reviewer logic)
        self.invoke_mock_hook("review_did_answer", card_id=card['id'], ease=ease)

        # Simulate state transition: move to next card or reveal answer if not already shown
        if self.answer_label.isHidden():
            self.reveal_answer()
        else:
            # Move to the next card
            self.current_card_index = (self.current_card_index + 1) % len(self.mock_cards)
            self.display_card()

    def show_ease_buttons(self):
        """Makes the ease buttons visible."""
        self.again_button.show()
        self.hard_button.show()
        self.good_button.show()
        self.easy_button.show()

    def hide_ease_buttons(self):
        """Hides the ease buttons."""
        self.again_button.hide()
        self.hard_button.hide()
        self.good_button.hide()
        self.easy_button.hide()

    def log_action(self, message):
        """Logs an action taken during the simulation."""
        self.session_actions.append(message)
        self.hooks_log_display.append(f"- {message}")
        self.hooks_log_display.ensureCursorVisible()

    def invoke_mock_hook(self, hook_name, **kwargs):
        """Simulates invoking a hook and logs it."""
        log_message = f"Hook '{hook_name}' invoked with args: {kwargs}"
        self.log_action(log_message)
        # In a real scenario, this would call the actual hook system.
        # For now, we just log.

class ConfigEditorWidget(QWidget):
    """Widget for editing Ankimon configuration as JSON."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.config_data = {} # Holds the current configuration

        layout = QVBoxLayout(self)

        title_label = QLabel("<h2>Configuration Editor</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Config file path display
        self.config_path_label = QLabel("Config File: (Not loaded)")
        self.config_path_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.config_path_label)

        # Splitter for editor and buttons
        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setStyleSheet("QSplitter::handle { background-color: #555555; }")

        # Top pane: JSON Editor
        editor_pane_widget = QWidget()
        editor_layout = QVBoxLayout(editor_pane_widget)

        self.config_editor = QPlainTextEdit()
        self.config_editor.setPlaceholderText("Ankimon configuration will be displayed and edited here as JSON.")
        self.config_editor.setStyleSheet("""
            QPlainTextEdit {
                background-color: #2d2d2d;
                border: 1px solid #555555;
                padding: 5px;
                font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
                font-size: 10pt;
                color: #f0f0f0;
            }
        """)
        editor_layout.addWidget(self.config_editor)
        splitter.addWidget(editor_pane_widget)

        # Bottom pane: Action Buttons
        button_layout = QHBoxLayout()
        self.load_config_button = QPushButton("Load Config")
        self.load_config_button.clicked.connect(self.load_config)
        self.save_config_button = QPushButton("Save Config")
        self.save_config_button.clicked.connect(self.save_config)
        self.save_config_button.setEnabled(False) # Disabled until config is loaded

        button_layout.addWidget(self.load_config_button)
        button_layout.addWidget(self.save_config_button)
        splitter.addWidget(QWidget()) # Placeholder for button layout in splitter
        splitter.widget(1).setLayout(button_layout) # Apply layout to the placeholder

        layout.addWidget(splitter)

        self.setStyleSheet("""
            QWidget { background-color: #2d2d2d; }
            QLabel { color: #f0f0f0; }
        """)

        # Attempt to load default config on initialization
        self.load_config()

    def load_config(self):
        """Loads configuration using MockAddonManager."""
        try:
            # In a real Anki environment, this would be mw.addonManager.getConfig("Ankimon")
            # For now, we use the mock.
            # The mock getConfig returns a dict, so we'll simulate loading it.
            # A real config file path would be needed for actual loading.
            # For this mock, we'll use a predefined structure.

            # Simulate loading from a file or default
            # For demonstration, let's use a hardcoded default config structure
            # that mimics what MockAddonManager might return.
            # In a real scenario, you'd use QFileDialog to pick a file.

            # Mocking the getConfig call to simulate loading
            # The actual config data is embedded within the mock AddonManager
            # For this example, let's assume a default structure if the mock doesn't provide it.
            # A more robust approach would be to have a default config file.

            # Let's simulate loading a default config if no file is specified or found
            # For now, we'll use a sample config directly.
            self.config_data = {
                "misc.leaderboard": False,
                "gui.pop_up_dialog_message_on_defeat": True,
                "trainer.name": "Ash",
                "gui.xp_bar_config": True,
                "gui.review_hp_bar_thickness": 2,
                "misc.discord_rich_presence_text": 1,
                "misc.language": 9,
                "battle.automatic_battle": 0,
                "battle.dmg_in_reviewer": True,
                "battle.cards_per_round": 2,
                "misc.YouShallNotPass_Ankimon_News": False,
                "misc.remove_level_cap": False,
            }

            # Update the config path label
            self.config_path_label.setText("Config File: (Mocked Default)")

            # Display the config in the editor
            self.config_editor.setPlainText(json.dumps(self.config_data, indent=2))
            self.save_config_button.setEnabled(True)
            self.parent_window.status_bar.showMessage("Default configuration loaded.")

        except Exception as e:
            self.config_path_label.setText("Config File: Error loading")
            self.config_editor.setPlainText(f"Error loading configuration: {e}")
            self.save_config_button.setEnabled(False)
            self.parent_window.status_bar.showMessage("Error loading configuration.")
            logger.error(f"Error loading config: {e}")

    def save_config(self):
        """Saves the current configuration using MockAddonManager."""
        try:
            new_config_text = self.config_editor.toPlainText()
            new_config_data = json.loads(new_config_text)

            # In a real Anki environment, this would be mw.addonManager.writeConfig("Ankimon", new_config_data)
            # For the mock, we'll just update the internal state and log.
            self.parent_window.mock_addon_manager.writeConfig("Ankimon", new_config_data) # Using the mock manager from parent
            self.config_data = new_config_data # Update internal state
            self.parent_window.status_bar.showMessage("Configuration saved successfully.")
            self.config_editor.setPlainText(json.dumps(self.config_data, indent=2)) # Reformat to ensure consistency

        except json.JSONDecodeError:
            self.parent_window.status_bar.showMessage("Error: Invalid JSON format. Please correct before saving.")
        except Exception as e:
            self.parent_window.status_bar.showMessage(f"Error saving configuration: {e}")
            logger.error(f"Error saving config: {e}")

class AnkimonTestApp(QMainWindow):
    """
    The main application window for the Ankimon Test Environment.
    Provides a GUI for discovering, running tests, simulating reviewer workflows,
    and viewing logs and configurations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ankimon Test Environment")
        self.setMinimumSize(900, 700)

        # --- Mock Objects Initialization ---
        # self.mock_collection = MockCollection()
        # self.mock_profile_manager = MockProfileManager()
        # self.mock_addon_manager = MockAddonManager()
        # self.mock_utils = MockUtils()
        # self.mock_reviewer = MockReviewer()
        # self.mock_reviewer_window = MockReviewerWindow()
        # self.mock_main_window = MockMainWindow(self)
        # self.mock_form = MockForm()
        # self.mock_logger = MockShowInfoLogger()
        # self.mock_translator = MockTranslator("en")

        # self.settings = MockAqtCollection()
        # self.ankimon_tracker = MockAnkimonTrackerWindow()
        # self.main_pokemon = MockPokemonObject()
        # self.enemy_pokemon = MockEnemyPokemon()
        # self.reviewer_manager = MockReviewerManager(
        #     self.settings, self.main_pokemon, self.enemy_pokemon, self.ankimon_tracker
        # )

        # --- GUI Setup ---
        self._setup_status_bar()
        self._setup_menu_bar()
        self._setup_central_widget()
        self._apply_theme()

        logger.info("Ankimon Test Environment GUI initialized.")

    def _setup_menu_bar(self):
        """Sets up the main menu bar for the application."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        exit_action = QAction("&Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tests Menu
        tests_menu = menu_bar.addMenu("&Tests")
        run_all_tests_action = QAction("Run &All Tests", self)
        run_all_tests_action.triggered.connect(self.run_all_tests_from_menu)
        tests_menu.addAction(run_all_tests_action)
        tests_menu.addSeparator()
        discover_tests_action = QAction("&Discover Tests", self)
        discover_tests_action.triggered.connect(self.discover_tests_from_menu)
        tests_menu.addAction(discover_tests_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = QAction("&About", self)
        about_action.triggered.connect(self.show_about_dialog)
        help_menu.addAction(about_action)

    def _setup_central_widget(self):
        """Sets up the central widget with tabbed navigation."""
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Create and add widgets for each tab
        self.test_browser_tab = TestBrowserWidget(self)
        self.reviewer_simulation_tab = ReviewerSimulationWidget(self)
        self.log_viewer_tab_widget = LogViewerWidget(self)
        self.config_editor_tab = ConfigEditorWidget(self)

        self.tab_widget.addTab(self.test_browser_tab, "Test Browser")
        self.tab_widget.addTab(self.reviewer_simulation_tab, "Reviewer Simulation")
        self.tab_widget.addTab(self.log_viewer_tab_widget.widget, "Logs")
        self.tab_widget.addTab(self.config_editor_tab, "Config Editor")

        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #555555; }
            QTabBar::tab {
                background: #3c3c3c;
                border: 1px solid #555555;
                border-bottom: none;
                padding: 8px;
                min-width: 100px;
                font-weight: bold;
                color: #f0f0f0;
            }
            QTabBar::tab:selected {
                background: #2d2d2d;
                border-color: #555555;
                border-bottom: 2px solid #2d2d2d;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)

    def _setup_status_bar(self):
        """Sets up the status bar at the bottom of the window."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _apply_theme(self):
        """Applies a basic theme to the main window."""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(60, 60, 60))
        palette.setColor(QPalette.ColorRole.WindowText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Base, QColor(45, 45, 45))
        palette.setColor(QPalette.ColorRole.AlternateBase, QColor(60, 60, 60))
        palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.ToolTipText, QColor(0, 0, 0))
        palette.setColor(QPalette.ColorRole.Text, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.Button, QColor(85, 85, 85))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(240, 240, 240))
        palette.setColor(QPalette.ColorRole.BrightText, QColor(255, 0, 0))
        palette.setColor(QPalette.ColorRole.Link, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(42, 130, 218))
        palette.setColor(QPalette.ColorRole.HighlightedText, QColor(240, 240, 240))
        self.setPalette(palette)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #3c3c3c;
            }
            QLabel {
                color: #f0f0f0;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #555555;
                border: none;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 10pt;
                margin: 4px 2px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #666666;
            }
            QStatusBar {
                background-color: #3c3c3c;
                font-weight: bold;
                color: #f0f0f0;
            }
        """)

    # --- Menu Actions ---
    def discover_tests_from_menu(self):
        """Triggers test discovery from the menu."""
        self.test_browser_tab.discover_tests()

    def run_all_tests_from_menu(self):
        """Triggers running all tests from the menu."""
        self.test_browser_tab.run_all_tests()

    def show_about_dialog(self):
        """Displays a simple about dialog."""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About Ankimon Test Environment")
        layout = QVBoxLayout(about_dialog)
        label = QLabel("Ankimon Test Environment\n\nVersion: 0.1.0\n\nDeveloped for Ankimon testing and simulation.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(about_dialog.accept)
        layout.addWidget(ok_button)
        about_dialog.exec()

    def closeEvent(self, event):
        """Handles the window close event."""
        logger.info("Closing Ankimon Test Environment.")
        if self.test_browser_tab:
            self.test_browser_tab.stop_all_tests()
        event.accept()

# --- Main Execution Logic ---
def main():
    global mw, app

    parser = argparse.ArgumentParser(description="Ankimon Test Environment")
    parser.add_argument('--full-anki', action='store_true', help='Run a full Anki-like interface')
    args = parser.parse_args()

    if not QApplication.instance():
        app = QApplication(sys.argv)
    else:
        app = QApplication.instance()

    mw = AnkimonTestApp()
    mw.show()

    app.exec()

if __name__ == "__main__":
    main()
