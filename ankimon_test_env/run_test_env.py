import sys
import os
import argparse
import logging
import subprocess
import importlib
import threading
from pathlib import Path

# --- PyQt6 Imports ---
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QTabWidget, QStatusBar, QDialog, QTextEdit, QPushButton,
    QListWidget, QListWidgetItem, QHBoxLayout, QSizePolicy
)
from PyQt6.QtCore import Qt, QObject, QSignalMapper, QVariant, QTimer, QThread, pyqtSignal, QCoreApplication
from PyQt6.QtGui import QPalette, QColor, QAction, QIcon

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

# --- Test Runner Logic ---

class TestRunnerThread(QThread):
    """
    Thread to run tests and emit output and status signals.
    """
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str, bool) # test_name, success

    def __init__(self, test_file_path, test_name):
        super().__init__()
        self.test_file_path = test_file_path
        self.test_name = test_name
        self._is_running = True

    def run(self):
        """Executes the test script."""
        self.output_signal.emit(f"--- Running test: {self.test_name} ---\n")
        try:
            # Use subprocess to run the test script
            # We need to ensure the Python interpreter used is the one running this script
            python_executable = sys.executable
            process = subprocess.Popen(
                [python_executable, str(self.test_file_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            # Read output in real-time
            while self._is_running:
                stdout_line = process.stdout.readline()
                if stdout_line:
                    self.output_signal.emit(stdout_line)
                stderr_line = process.stderr.readline()
                if stderr_line:
                    self.output_signal.emit(f"ERROR: {stderr_line}")

                # Check if process has finished
                if process.poll() is not None:
                    break

                # Small sleep to prevent busy-waiting
                self.msleep(50)

            # If the thread was stopped prematurely
            if not self._is_running:
                process.terminate() # Attempt to terminate the process
                process.wait()
                self.output_signal.emit("\n--- Test stopped by user ---\n")
                self.finished_signal.emit(self.test_name, False)
                return

            # Process completion
            stdout_remaining, stderr_remaining = process.communicate()
            if stdout_remaining:
                self.output_signal.emit(stdout_remaining)
            if stderr_remaining:
                self.output_signal.emit(f"ERROR: {stderr_remaining}")

            if process.returncode == 0:
                self.output_signal.emit(f"\n--- Test '{self.test_name}' PASSED ---\n")
                self.finished_signal.emit(self.test_name, True)
            else:
                self.output_signal.emit(f"\n--- Test '{self.test_name}' FAILED (Exit code: {process.returncode}) ---\n")
                self.finished_signal.emit(self.test_name, False)

        except FileNotFoundError:
            error_msg = f"ERROR: Test file not found at {self.test_file_path}"
            self.output_signal.emit(error_msg)
            self.finished_signal.emit(self.test_name, False)
        except Exception as e:
            error_msg = f"ERROR: An unexpected error occurred while running test '{self.test_name}': {e}"
            self.output_signal.emit(error_msg)
            self.finished_signal.emit(self.test_name, False)

    def stop(self):
        """Signals the thread to stop."""
        self._is_running = False

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
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                padding: 5px;
                font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
                font-size: 10pt;
            }
        """)

    def emit(self, record):
        msg = self.format(record)
        self.widget.append(msg)

class TestBrowserWidget(QWidget):
    """Widget for browsing and running tests."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent # Store reference to the main window
        self.test_threads = {} # To keep track of running test threads

        layout = QVBoxLayout(self)

        # Title
        title_label = QLabel("<h2>Test Browser</h2>")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Test Directory Label
        dir_label = QLabel(f"<b>Test Directory:</b> {os.path.abspath(ANKIMON_TESTS_DIR)}")
        dir_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(dir_label)

        # Test List and Controls
        self.test_list_widget = QListWidget()
        self.test_list_widget.setAlternatingRowColors(True)
        self.test_list_widget.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                padding: 5px;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 5px;
                border-bottom: 1px solid #eeeeee;
            }
            QListWidget::item:selected {
                background-color: #cce5ff;
                color: #004085;
            }
            QListWidget::item:hover {
                background-color: #f8f9fa;
            }
        """)
        layout.addWidget(self.test_list_widget)

        # Buttons for Test Actions
        button_layout = QHBoxLayout()
        self.discover_button = QPushButton("Discover Tests")
        self.discover_button.clicked.connect(self.discover_tests)
        self.run_all_button = QPushButton("Run All")
        self.run_all_button.clicked.connect(self.run_all_tests)
        self.stop_all_button = QPushButton("Stop All")
        self.stop_all_button.clicked.connect(self.stop_all_tests)
        self.stop_all_button.setEnabled(False) # Initially disabled

        button_layout.addWidget(self.discover_button)
        button_layout.addWidget(self.run_all_button)
        button_layout.addWidget(self.stop_all_button)
        layout.addLayout(button_layout)

        # Output Area
        self.output_area = QTextEdit()
        self.output_area.setReadOnly(True)
        self.output_area.setPlaceholderText("Test execution output will appear here...")
        self.output_area.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #cccccc;
                padding: 5px;
                font-family: Consolas, Monaco, 'Andale Mono', 'Ubuntu Mono', monospace;
                font-size: 10pt;
            }
        """)
        self.output_area.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        layout.addWidget(self.output_area)

        # Status Label
        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.status_label)

        self.setStyleSheet("""
            QWidget { background-color: #e0f7fa; }
            QLabel { color: #00796b; }
        """)

        # Initial discovery on load
        self.discover_tests()

    def discover_tests(self):
        """Discovers .py files in the ANKIMON_TESTS_DIR."""
        self.test_list_widget.clear()
        self.output_area.clear()
        self.status_label.setText("Status: Discovering tests...")
        self.parent_window.statusBar.showMessage("Discovering tests...")

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
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsSelectable) # Make it non-selectable
                self.test_list_widget.addItem(item)
                self.status_label.setText("Status: No tests found.")
            else:
                self.status_label.setText(f"Status: Found {self.test_list_widget.count()} tests.")
                self.parent_window.statusBar.showMessage(f"Found {self.test_list_widget.count()} tests.")

        except Exception as e:
            error_msg = f"Error during test discovery: {e}"
            self.output_area.append(error_msg)
            self.status_label.setText("Status: Error during discovery.")
            self.parent_window.statusBar.showMessage("Error during test discovery.")
            logger.error(error_msg)

    def run_test(self, test_file_path, test_name):
        """Starts a test in a separate thread."""
        if test_file_path in self.test_threads and self.test_threads[test_file_path].isRunning():
            self.output_area.append(f"Test '{test_name}' is already running.")
            return

        thread = TestRunnerThread(test_file_path, test_name)
        thread.output_signal.connect(self.append_output)
        thread.finished_signal.connect(self.handle_test_finish)
        self.test_threads[test_file_path] = thread
        thread.start()
        self.status_label.setText(f"Status: Running '{test_name}'...")
        self.parent_window.statusBar.showMessage(f"Running '{test_name}'...")
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
        self.parent_window.statusBar.showMessage("Starting all tests...")
        self.run_all_button.setEnabled(False)
        self.discover_button.setEnabled(False)
        self.stop_all_button.setEnabled(True)

        for i in range(self.test_list_widget.count()):
            item = self.test_list_widget.item(i)
            test_name = item.text()
            test_file_path = item.data(Qt.ItemDataRole.UserRole)

            if test_file_path and "No tests found" not in test_name:
                self.run_test(test_file_path, test_name)
                # Wait for the current test to finish before starting the next one
                # This is a simple sequential execution. For parallel, this would be different.
                if test_file_path in self.test_threads:
                    self.test_threads[test_file_path].wait() # Wait for this thread to complete

        self.status_label.setText("Status: All tests finished.")
        self.parent_window.statusBar.showMessage("All tests finished.")
        self.run_all_button.setEnabled(True)
        self.discover_button.setEnabled(True)
        self.stop_all_button.setEnabled(False)

    def stop_all_tests(self):
        """Stops all currently running tests."""
        self.status_label.setText("Status: Stopping tests...")
        self.parent_window.statusBar.showMessage("Stopping tests...")
        for test_file_path, thread in self.test_threads.items():
            if thread.isRunning():
                thread.stop()
                thread.wait() # Wait for the thread to actually stop
        self.test_threads.clear()
        self.status_label.setText("Status: All tests stopped.")
        self.parent_window.statusBar.showMessage("All tests stopped.")
        self.run_all_button.setEnabled(True)
        self.discover_button.setEnabled(True)
        self.stop_all_button.setEnabled(False)

    def append_output(self, text):
        """Appends text to the output area."""
        self.output_area.insertPlainText(text)
        self.output_area.ensureCursorVisible() # Auto-scroll to the bottom

    def handle_test_finish(self, test_name, success):
        """Updates UI when a test finishes."""
        # Find the item in the list and update its appearance
        for i in range(self.test_list_widget.count()):
            item = self.test_list_widget.item(i)
            if item.text() == test_name:
                if success:
                    item.setForeground(QColor("green"))
                    item.setText(f"{test_name} (PASSED)")
                else:
                    item.setForeground(QColor("red"))
                    item.setText(f"{test_name} (FAILED)")
                break

        # Check if all tests are done to re-enable buttons
        all_tests_finished = True
        for test_file_path, thread in self.test_threads.items():
            if thread.isRunning():
                all_tests_finished = False
                break

        if all_tests_finished:
            self.status_label.setText("Status: All tests finished.")
            self.parent_window.statusBar.showMessage("All tests finished.")
            self.run_all_button.setEnabled(True)
            self.discover_button.setEnabled(True)
            self.stop_all_button.setEnabled(False)
        else:
            self.status_label.setText(f"Status: Test '{test_name}' finished. More tests running...")
            self.parent_window.statusBar.showMessage(f"Test '{test_name}' finished. More tests running...")


class ReviewerSimulationWidget(QWidget):
    """Placeholder for the simulated reviewer interface."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("<h2>Simulated Reviewer</h2>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(QLabel("This area will simulate the Ankimon reviewer workflow."))
        layout.addStretch()
        self.setStyleSheet("""
            QWidget { background-color: #fff9c4; }
            QLabel { color: #f57f17; }
        """)

class ConfigEditorWidget(QWidget):
    """Placeholder for the configuration editor/viewer."""
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        label = QLabel("<h2>Configuration Editor</h2>")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addWidget(QLabel("Configuration display and editing will be available here."))
        layout.addStretch()
        self.setStyleSheet("""
            QWidget { background-color: #e8f5e9; }
            QLabel { color: #2e7d32; }
        """)

class AnkimonTestApp(QMainWindow):
    """
    The main application window for the Ankimon Test Environment.
    Provides a GUI for discovering, running tests, simulating reviewer workflows,
    and viewing logs and configurations.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ankimon Test Environment")
        self.setMinimumSize(900, 700) # Increased size for better layout

        # --- Mock Objects Initialization ---
        self.mock_collection = MockCollection()
        self.mock_profile_manager = MockProfileManager()
        self.mock_addon_manager = MockAddonManager()
        self.mock_utils = MockUtils()
        self.mock_reviewer = MockReviewer()
        self.mock_reviewer_window = MockReviewerWindow()
        self.mock_main_window = MockMainWindow(self) # Pass self as parent if needed
        self.mock_form = MockForm()
        self.mock_logger = MockShowInfoLogger()
        self.mock_translator = MockTranslator("en") # Default to English

        # Initialize Ankimon's core components with mocks
        self.settings = MockAqtCollection()
        self.ankimon_tracker = MockAnkimonTrackerWindow()
        self.main_pokemon = MockPokemonObject()
        self.enemy_pokemon = MockEnemyPokemon()
        self.reviewer_manager = MockReviewerManager(
            self.settings, self.main_pokemon, self.enemy_pokemon, self.ankimon_tracker
        )

        # --- GUI Setup ---
        self._setup_menu_bar()
        self._setup_central_widget()
        self._setup_status_bar()

        # Set a default theme
        self._apply_theme()

        logger.info("Ankimon Test Environment GUI initialized.")

    def _setup_menu_bar(self):
        """Sets up the main menu bar for the application."""
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("&File")
        exit_action = MockAction("&Exit")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Tests Menu
        tests_menu = menu_bar.addMenu("&Tests")
        run_all_tests_action = MockAction("Run &All Tests")
        run_all_tests_action.triggered.connect(self.run_all_tests_from_menu) # Connect to the TestBrowserWidget method
        tests_menu.addAction(run_all_tests_action)
        tests_menu.addSeparator()
        discover_tests_action = MockAction("&Discover Tests")
        discover_tests_action.triggered.connect(self.discover_tests_from_menu) # Connect to the TestBrowserWidget method
        tests_menu.addAction(discover_tests_action)

        # Help Menu
        help_menu = menu_bar.addMenu("&Help")
        about_action = MockAction("&About")
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
        self.test_browser_tab = TestBrowserWidget(self) # Pass self (the main window)
        self.reviewer_simulation_tab = ReviewerSimulationWidget()
        self.log_viewer_tab_widget = LogViewerWidget(self) # Instantiate the log handler
        self.config_editor_tab = ConfigEditorWidget()

        self.tab_widget.addTab(self.test_browser_tab, "Test Browser")
        self.tab_widget.addTab(self.reviewer_simulation_tab, "Reviewer Simulation")
        self.tab_widget.addTab(self.log_viewer_tab_widget.widget, "Logs") # Add the QTextEdit widget
        self.tab_widget.addTab(self.config_editor_tab, "Config Editor")

        # Apply styling to tabs for better visual separation
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane { border: 1px solid #cccccc; }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #cccccc;
                border-bottom: none;
                padding: 8px;
                min-width: 100px;
                font-weight: bold;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-color: #999999;
                border-bottom: 2px solid #ffffff;
            }
            QTabBar::tab:!selected {
                margin-top: 2px;
            }
        """)

    def _setup_status_bar(self):
        """Sets up the status bar at the bottom of the window."""
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("Ready")

    def _apply_theme(self):
        """Applies a basic theme to the main window."""
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(245, 245, 245)) # Light grey background
        palette.setColor(QPalette.ColorRole.WindowText, QColor(50, 50, 50)) # Dark text
        palette.setColor(QPalette.ColorRole.Button, QColor(220, 220, 220)) # Lighter buttons
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30)) # Dark button text
        self.setPalette(palette)

        # Apply some general styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QLabel {
                color: #333333;
                font-size: 11pt;
            }
            QPushButton {
                background-color: #4CAF50; /* Green */
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
                background-color: #45a049;
            }
            QStatusBar {
                background-color: #e0e0e0;
                font-weight: bold;
            }
        """)

    # --- Menu Actions ---
    # These methods now delegate to the TestBrowserWidget
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
        # Ensure any running threads are stopped before closing
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

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
