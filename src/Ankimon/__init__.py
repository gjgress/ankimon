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
    PYQT6_AVAILABLE = False
    
except ImportError:
    PYQT6_AVAILABLE = False
    print("PyQt6 not found. Mocks will use placeholder classes. Please install PyQt6 (`pip install PyQt6`).")

    # Define placeholder classes if PyQt6 is not installed
    class DummyCallable:
        def __call__(self, *args, **kwargs):
            return self
        def __getattr__(self, name):
            if name.startswith("__"):
                raise AttributeError
            return self

    class MockWebEngineView:
        def setHtml(self, html):
            print(f"Placeholder QWebEngineView setHtml: {html[:50]}...")
        def show(self):
            print("Placeholder QWebEngineView show")

    class MockReviewer:
        def __init__(self, parent=None):
            print("Placeholder MockReviewer init")
            self.web = MockWebEngineView()
        def _showQuestion(self, card):
            print(f"Placeholder MockReviewer _showQuestion for card: {card.id}")
            self.web.setHtml(f"<h1>Question: {card.question()}</h1>")

    class MockAddonManager:
        def __init__(self, path):
            print(f"Placeholder MockAddonManager init with path: {path}")

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
