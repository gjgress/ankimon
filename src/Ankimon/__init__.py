import sys
import types
import unittest
from unittest.mock import patch, MagicMock
import os
import glob
from pathlib import Path
import shutil
import atexit
import json
import base64

# --- PyQt6 Imports ---
# Ensure a consistent import order for Qt components
try:
    from PyQt6.QtWidgets import (
        QApplication, QWidget, QLabel, QPushButton, QVBoxLayout, QMainWindow,
        QMenuBar, QMenu, QAction, QFrame, QHBoxLayout, QSizePolicy
    )
    from PyQt6.QtCore import Qt, QUrl, QTimer, pyqtSignal
    from PyQt6.QtGui import QFont, QColor, QKeySequence, QPixmap, QFontDatabase, QGuiApplication
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage, QWebEngineSettings
    PYQT6_AVAILABLE = True
    print("PyQt6 found. Using actual Qt classes where possible in mocks.")
except ImportError:
    PYQT6_AVAILABLE = False
    print("PyQt6 not found. Mocks will use placeholder classes. Please install PyQt6 (`pip install PyQt6`).")

    # Define placeholder classes if PyQt6 is not installed
    class QWidget:
        def __init__(self, parent=None): print("Placeholder QWidget init")
        def setLayout(self, layout): print("Placeholder QWidget setLayout")
        def layout(self): return None
        def show(self): print("Placeholder QWidget show")
        def hide(self): print("Placeholder QWidget hide")
        def setWindowTitle(self, title): print(f"Placeholder QWidget setWindowTitle: {title}")
        def setGeometry(self, x, y, w, h): print(f"Placeholder QWidget setGeometry: {x},{y},{w},{h}")
        def setCentralWidget(self, widget): print("Placeholder QWidget setCentralWidget")
        def setMenuBar(self, menu_bar): print("Placeholder QWidget setMenuBar")
        def setStatusBar(self, status_bar): print("Placeholder QWidget setStatusBar")
        def addAction(self, action): print(f"Placeholder QWidget addAction: {action}")
        def findChild(self, cls): return None # For HUD placeholder
        def setObjectName(self, name): pass
        def setStyleSheet(self, style): print(f"Placeholder QWidget setStyleSheet: {style}")
        def setMinimumHeight(self, height): pass
        def deleteLater(self): print("Placeholder QWidget deleteLater")

    class QLabel(QWidget):
        def __init__(self, text="", parent=None): super().__init__(parent); self.setText(text); print(f"Placeholder QLabel init: {text}")
        def setText(self, text): print(f"Placeholder QLabel setText: {text}")
        def setAlignment(self, alignment): print(f"Placeholder QLabel setAlignment: {alignment}")
        def setFont(self, font): print(f"Placeholder QLabel setFont: {font}")
        def hide(self): print("Placeholder QLabel hide"); super().hide()
        def show(self): print("Placeholder QLabel show"); super().show()

    class QPushButton(QWidget):
        def __init__(self, text="", parent=None): super().__init__(parent); self._text = text; print(f"Placeholder QPushButton init: {text}")
        def clicked_connect(self, slot): print(f"Placeholder QPushButton connect: {slot}") # Corrected method name
        def show(self): print("Placeholder QPushButton show"); super().show()
        def hide(self): print("Placeholder QPushButton hide"); super().hide()
        def text(self): return self._text

    class QVBoxLayout(QWidget):
        def __init__(self, parent=None): super().__init__(parent); print("Placeholder QVBoxLayout init")
        def addWidget(self, widget): print(f"Placeholder QVBoxLayout addWidget: {widget}")
        def addLayout(self, layout): print(f"Placeholder QVBoxLayout addLayout: {layout}")
        def count(self): return 0
        def itemAt(self, i): return None

    class QHBoxLayout(QVBoxLayout): pass # Inherit from QVBoxLayout

    class QFrame(QWidget):
        def __init__(self, parent=None): super().__init__(parent); print("Placeholder QFrame init")
        def setMinimumHeight(self, height): print(f"Placeholder QFrame setMinimumHeight: {height}")

    class QSizePolicy:
        Fixed = 0
        Preferred = 1

    class QDialog(QWidget):
        def __init__(self, parent=None): super().__init__(parent); print("Placeholder QDialog init")
        def exec(self): print("Placeholder QDialog exec"); return 0

    class QMenuBar(QWidget):
        def __init__(self): print("Placeholder QMenuBar init")
        def addMenu(self, title): return MockMenu(title) # MockMenu is defined below

    class QMenu(QWidget):
        def __init__(self, title): self._title = title; print(f"Placeholder QMenu init: {title}")
        def addAction(self, action): print(f"Placeholder QMenu addAction: {action}")
        def text(self): return self._text

    class QAction:
        def __init__(self, text, parent=None): self._text = text; print(f"Placeholder QAction init: {text}")
        def text(self): return self._text
        def triggered(self): return MockSignal() # Simulate signal
        def connect(self, slot): print(f"Placeholder QAction connect: {slot}")

    class QFont: pass
    class QColor: pass

    class QUrl:
        @staticmethod
        def fromLocalFile(path): return path

    class QTimer:
        def __init__(self): print("Placeholder QTimer init")
        def singleShot(self, ms, callback): print(f"Placeholder QTimer singleShot: {ms}ms")

    class pyqtSignal:
        def connect(self, slot): print(f"Placeholder pyqtSignal connect: {slot}")
        def emit(self): print("Placeholder pyqtSignal emit")

    class QApplication:
        @staticmethod
        def instance(): return None
        def __init__(self, args): print("Placeholder QApplication init")
        def processEvents(self): pass
        def quit(self): pass
        def exec(self): print("Placeholder QApplication exec"); return 0

    # Define MockMenu here as it's used by QMenuBar placeholder
    class MockMenu(QWidget):
        def __init__(self, title): self._title = title; print(f"MockMenu init: {title}")
        def addAction(self, action): print(f"MockMenu addAction: {action}")
        def text(self): return self._text

    # Define QStatusBar placeholder
    class QStatusBar(QWidget):
        def __init__(self): print("Placeholder QStatusBar init")
        def showMessage(self, message, timeout=0): print(f"Placeholder QStatusBar showMessage: {message}")

    # Define MockMainWindow placeholder
    class MockMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.mw = self
            self.form = QWidget()
            self.setCentralWidget(self.form)
            self.form.vbox = QVBoxLayout(self.form)

            self.col = DummyCallable()
            self.col.conf = {}
            # The scheduler needs a reference to the main window to interact with the reviewer
            self.col.sched = MockScheduler(self.mw) 

            self.reviewer = MockReviewer(parent=self.form) # Pass form as parent
            self.form.vbox.addWidget(self.reviewer.web) # Add reviewer's webview to main window layout

            self.addonManager = MockAddonManager(Path(__file__).parent.parent.resolve())
            self.pm = DummyCallable()
            self.pm.name = "test-profile"
            self.menubar = self.menuBar()
            self.form.menubar = self.menubar
            # Use the placeholder QMenu defined above
            self.pokemenu = QMenu("Ankimon (Mock)", self)
            self.menubar.addMenu(self.pokemenu)
            start_review_action = QAction("Start Review (Mock)", self)
            start_review_action.triggered.connect(self._start_mock_review)
            self.pokemenu.addAction(start_review_action)

        def _start_mock_review(self):
            print("Starting mock review!")
            # Hide other widgets if any, and show reviewer's webview
            self.reviewer.web.show()
            # Trigger the scheduler to get a card
            self.col.sched.startReview()

        def __getattr__(self, name):
            if name.startswith("__"):
                raise AttributeError
            return DummyCallable()


# --- Mocking Anki/AQT specific modules ---
# Import the mock implementations provided earlier.
try:
    from ankimon_test_env.mock_anki.collection import Collection as MockAnkiCollection
    from ankimon_test_env.mock_anki.collection import MockCard, MockNote, MockScheduler
    from ankimon_test_env.mock_aqt.reviewer import Reviewer as MockAqtReviewer
    from ankimon_test_env.mock_aqt.reviewer import MockReviewerWindow # Import the window class directly
except ImportError as e:
    print(f"Error importing mock modules: {e}")
    print("Please ensure mock files are correctly placed and accessible.")
    # Define dummy classes if imports fail, to allow script execution to continue
    class MockAnkiCollection:
        def __init__(self): print("Dummy MockAnkiCollection initialized."); self.sched = MockScheduler(None) # Pass None initially
        def get_config(self, key, default=None): return default
        def set_config(self, key, value): pass
        def sched_ver(self): return 3
        def v3_scheduler(self): return True
        def get_card(self, card_id): return MockCard(card_id)
        def get_card_info(self, card_id): return None
        def search_cards(self, query): return []
        def get_deck_names(self): return {"1": "Default"}
        def get_deck_id(self, deck_name): return 1
        def get_deck_by_id(self, deck__id): return {"name": "Default"}
        def create_note(self, note_type_name, fields): return MockNote()
        def create_card(self, note, template_index=0): return MockCard()

    class MockAqtReviewer:
        def __init__(self, mw, collection): print("Dummy MockAqtReviewer initialized."); self.reviewer_window = MockReviewerWindow(mw, collection)
        def show(self): print("Dummy MockAqtReviewer: show called."); self.reviewer_window.show()
        def exec(self): print("Dummy MockAqtReviewer: exec called."); return 0
        def load_cards(self): print("Dummy MockAqtReviewer: load_cards called."); self.reviewer_window.load_next_card()
        def answer_card(self, ease): print(f"Dummy MockAqtReviewer: answer_card called with ease {ease}."); self.reviewer_window.answer_card(ease)
        def show_answer(self): print("Dummy MockAqtReviewer: show_answer called."); self.reviewer_window.show_answer()

    class MockCard:
        def __init__(self, card_id, question="Mock Q", answer="Mock A"): self.id = card_id; self._question = question; self._answer = answer
        def question(self): return self._question
        def answer(self): return self._answer
        def note(self): return MockNote()
    class MockNote:
        def __init__(self, note_id=123, fields=None): self.id = note_id; self._fields = fields if fields else ["F1", "F2"]
        def has_tag(self, tag): return False
        def fields(self): return self._fields
    class MockScheduler:
        def __init__(self, mw_instance): self.mw = mw_instance; self._cards_in_queue = [MockCard(1)]; self.new_count = 1; self.learning_count = 0; self.review_count = 0
        def get_queued_cards(self): return MockQueuedCards([MockCard(1)])
        def answerButtons(self, card): return 4
        def describe_next_states(self, states): return ["Again", "Hard", "Good", "Easy"]
        def answerCard(self, card, ease): print(f"Dummy MockScheduler answerCard: {card.id}, ease {ease}")
        def startReview(self): print("[MOCK Scheduler] startReview() called."); card = MockCard(1); self.mw.reviewer._showQuestion(card) if self.mw and self.mw.reviewer else print("Cannot start review: mw or reviewer not available.")
    class MockQueuedCards:
        def __init__(self, cards): self.cards = cards
        def top_card(self): return self.cards[0] if self.cards else None
    class MockReviewerWindow:
        def __init__(self, mw, collection): print("Dummy MockReviewerWindow init"); self.mw = mw; self.collection = collection
        def load_next_card(self): print("Dummy MockReviewerWindow load_next_card")
        def show_answer(self): print("Dummy MockReviewerWindow show_answer")
        def answer_card(self, ease): print(f"Dummy MockReviewerWindow answer_card: {ease}")
        def show(self): print("Dummy MockReviewerWindow show")
        def exec(self): print("Dummy MockReviewerWindow exec"); return 0
        def question_shown(self): return MockSignal()
        def answer_shown(self): return MockSignal()
        def card_answered(self): return MockSignal()
    class MockSignal:
        def connect(self, slot): print(f"Dummy MockSignal connect: {slot}")
        def emit(self): print("Dummy MockSignal emit")

# --- Setup Anki/AQT Mocks for sys.modules ---
def setup_ankiaqt_mocks():
    """
    Creates and injects mock versions of anki and aqt modules into sys.modules
    to prevent ImportErrors during testing.
    """
    print("Setting up anki/aqt mocks...")

    mock_anki = types.ModuleType("anki")
    mock_anki.collection = types.ModuleType("anki.collection")
    mock_anki.sched = types.ModuleType("anki.sched")
    mock_anki.utils = types.ModuleType("anki.utils")
    mock_anki.collection.Collection = MockAnkiCollection
    mock_anki.collection.Card = MockCard
    mock_anki.collection.Note = MockNote

    mock_aqt = types.ModuleType("aqt")
    mock_aqt.gui_hooks = types.ModuleType("aqt.gui_hooks")
    mock_aqt.main = types.ModuleType("aqt.main")
    mock_aqt.forms = types.ModuleType("aqt.forms")
    mock_aqt.forms.reviewer = types.ModuleType("aqt.forms.reviewer")
    mock_aqt.forms.reviewer.Reviewer = MockAqtReviewer

    mock_aqt.dialogs = types.ModuleType("aqt.dialogs")
    mock_aqt.dialogs.showInfo = lambda msg: print(f"Mock aqt.dialogs.showInfo: {msg}")
    mock_aqt.dialogs.showWarning = lambda msg: print(f"Mock aqt.dialogs.showWarning: {msg}")

    mock_aqt.utils = types.ModuleType("aqt.utils")
    mock_aqt.utils.maybeHook = lambda x: x

    mock_aqt.browser = types.ModuleType("aqt.browser")
    mock_aqt.browser.AnkiBrowser = MagicMock()

    mock_aqt.qt = types.ModuleType("aqt.qt")
    mock_aqt.qt.QtCore = types.ModuleType("aqt.qt.QtCore")
    mock_aqt.qt.QtGui = types.ModuleType("aqt.qt.QtGui")
    mock_aqt.qt.QtWidgets = types.ModuleType("aqt.qt.QtWidgets")
    mock_aqt.qt.QtWidgets.QApplication = QApplication
    mock_aqt.qt.QtWidgets.QMainWindow = QMainWindow
    mock_aqt.qt.QtWidgets.QWidget = QWidget
    mock_aqt.qt.QtWidgets.QAction = QAction
    mock_aqt.qt.QtWidgets.QMenu = QMenu
    mock_aqt.qt.QtWidgets.QMenuBar = QMenuBar
    # Use the placeholder QStatusBar defined in the except block if PyQt6 is not available
    mock_aqt.qt.QtWidgets.QStatusBar = QStatusBar if PYQT6_AVAILABLE else QStatusBar
    mock_aqt.qt.QtWidgets.QDialog = QDialog
    mock_aqt.qt.QtWidgets.QVBoxLayout = QVBoxLayout
    mock_aqt.qt.QtWidgets.QLabel = QLabel
    mock_aqt.qt.QtWidgets.QPushButton = QPushButton
    mock_aqt.qt.QtWidgets.QFrame = QFrame
    mock_aqt.qt.QtWidgets.QHBoxLayout = QHBoxLayout
    mock_aqt.qt.QtWidgets.QSizePolicy = QSizePolicy
    mock_aqt.qt.QtWidgets.QMessageBox = MagicMock()
    mock_aqt.qt.QtWidgets.QFont = QFont
    mock_aqt.qt.QtWidgets.QColor = QColor

    mock_aqt.qt.QtWebEngineWidgets = types.ModuleType("aqt.qt.QtWebEngineWidgets")
    mock_aqt.qt.QtWebEngineWidgets.QWebEngineView = QWebEngineView
    mock_aqt.qt.QtWebEngineWidgets.QWebEnginePage = QWebEnginePage
    mock_aqt.qt.QtWebEngineWidgets.QWebEngineSettings = QWebEngineSettings

    sys.modules["anki"] = mock_anki
    sys.modules["anki.collection"] = mock_anki.collection
    sys.modules["anki.sched"] = mock_anki.sched
    sys.modules["anki.utils"] = mock_anki.utils

    sys.modules["aqt"] = mock_aqt
    sys.modules["aqt.gui_hooks"] = mock_aqt.gui_hooks
    sys.modules["aqt.main"] = mock_aqt.main
    sys.modules["aqt.forms"] = mock_aqt.forms
    sys.modules["aqt.forms.reviewer"] = mock_aqt.forms.reviewer
    sys.modules["aqt.dialogs"] = mock_aqt.dialogs
    sys.modules["aqt.utils"] = mock_aqt.utils
    sys.modules["aqt.browser"] = mock_aqt.browser
    sys.modules["aqt.qt"] = mock_aqt.qt
    sys.modules["aqt.qt.QtCore"] = mock_aqt.qt.QtCore
    sys.modules["aqt.qt.QtGui"] = mock_aqt.qt.QtGui
    sys.modules["aqt.qt.QtWidgets"] = mock_aqt.qt.QtWidgets
    sys.modules["aqt.qt.QtWebEngineWidgets"] = mock_aqt.qt.QtWebEngineWidgets

    print("Anki/AQT mocks injected into sys.modules.")

# --- Add-on Loading ---
# This is where we'll import and execute your add-on's __init__.py
ANKIMON_ADDON_MODULE = None # Global to hold the loaded add-on module

def load_ankimon_addon():
    """
    Imports and executes the Ankimon add-on's __init__.py to set up menus, hooks, etc.
    """
    global ANKIMON_ADDON_MODULE
    global mw # Access the global mw to check for menus
    print("\n--- Loading Ankimon Add-on Initialization ---")
    try:
        # --- IMPORTANT ---
        # This import path assumes your Ankimon code is structured as:
        # your_project_root/src/Ankimon/__init__.py
        # Adjust the path if your structure is different.
        
        # Add 'src' to sys.path if it's not already there
        src_path = Path(__file__).parent.parent / 'src'
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
            print(f"Added '{src_path}' to sys.path for add-on import.")

        import Ankimon # This will execute src/Ankimon/__init__.py

        ANKIMON_ADDON_MODULE = Ankimon # Store the module if needed later
        print("Ankimon add-on __init__.py executed successfully.")

        # The __init__.py file itself should handle menu creation and hook registration.
        # We don't need to manually add menu items here if __init__.py does it.
        # However, we can verify if the menu was created.

        # Check if Ankimon menu was added (assuming __init__.py does this)
        if mw and hasattr(mw, 'menu_bar') and mw.menu_bar:
            found_menu = False
            # Iterate through the menus added to the menubar
            for menu in mw.menu_bar.findChildren(QMenu):
                if "Ankimon" in menu.title(): # Check for "Ankimon (Test)" or similar
                    found_menu = True
                    print("Verified: Ankimon menu found in mock main window.")
                    break
            if not found_menu:
                print("Warning: Ankimon menu not found. Ensure __init__.py creates it.")
        else:
            print("Warning: Mock Main Window or menu bar not available to verify Ankimon menu.")

    except ImportError as e:
        print(f"Error importing Ankimon add-on: {e}")
        print("Please ensure 'src/Ankimon/__init__.py' is correctly placed and importable.")
        print("Also, check that all dependencies within Ankimon's __init__.py are mocked or available.")
    except Exception as e:
        print(f"An unexpected error occurred during Ankimon add-on loading: {e}")
        import traceback
        traceback.print_exc()

# --- Main Test Environment ---

def run_test_environment():
    """
    Sets up and runs the Ankimon test environment.
    """
    global app_instance, mw

    print("\n--- Starting Test Environment Setup ---")

    # Ensure QApplication instance exists
    if QApplication.instance() is None:
        app_instance = QApplication(sys.argv)
    else:
        app_instance = QApplication.instance()

    # Setup mocks for Anki and AQT modules BEFORE loading the add-on
    setup_ankiaqt_mocks()

    # Create the main window (which will host menus and potentially the reviewer)
    mw = MockMainWindow()

    # Load the add-on's initialization code
    load_ankimon_addon()

    # Show the main window
    mw.show()
    print("\n--- Test Environment Setup Complete ---")
    print("Ankimon menu should be visible in the mock main window.")
    print("Click 'Ankimon (Mock)' -> 'Start Review (Mock)' to start a mock review session.")

if __name__ == '__main__':
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)

    run_test_environment()

    print("\nStarting Qt event loop...")
    # Run the Qt application's event loop
    sys.exit(app.exec())
