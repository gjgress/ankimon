import sys
import os
import argparse
import logging
from pathlib import Path

# --- Argument Parsing ---
parser = argparse.ArgumentParser(description="Ankimon Test Environment")
parser.add_argument('--full-anki', action='store_true', help='Run a full Anki-like interface')
args = parser.parse_args()

# --- Logging Configuration ---
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format)
logger = logging.getLogger(__name__)

# --- GUI Classes (defined if in GUI mode) ---
class AnkiApp:  # Placeholder for headless mode
    def __init__(self):
        logger.info("Running in headless mode.")

# --- Main Execution Logic ---
def main():
    global AnkiApp

    if args.full_anki:
        try:
            from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton
            from PyQt6.QtCore import Qt
            from PyQt6.QtGui import QPalette, QColor
        except ImportError as e:
            logger.critical(f"PyQt6 GUI libraries not found: {e}. Cannot run in --full-anki mode.")
            sys.exit(1)

        class QTextEditLogger(logging.Handler):
            def __init__(self, parent):
                super().__init__()
                self.widget = QTextEdit(parent)
                self.widget.setReadOnly(True)

            def emit(self, record):
                msg = self.format(record)
                self.widget.append(msg)

        class AnkiApp(QMainWindow):
            def __init__(self):
                super().__init__()
                self.setWindowTitle("Ankimon Test Environment")
                self.setMinimumSize(800, 600)

                # Set a light theme
                palette = self.palette()
                palette.setColor(QPalette.ColorRole.Window, QColor(240, 240, 240))
                self.setPalette(palette)

                # Central Widget and Layout
                central_widget = QWidget()
                self.setCentralWidget(central_widget)
                layout = QVBoxLayout(central_widget)

                # Welcome Label
                welcome_label = QLabel("<h2>Welcome to the Ankimon Test Environment</h2>")
                welcome_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                layout.addWidget(welcome_label)

                # Log Viewer
                log_text_box = QTextEditLogger(self)
                log_text_box.setFormatter(logging.Formatter(log_format))
                logging.getLogger().addHandler(log_text_box)
                logging.getLogger().setLevel(logging.INFO)
                layout.addWidget(log_text_box.widget)

                # Action Buttons
                button_layout = QVBoxLayout()
                run_tests_button = QPushButton("Run Tests (Not Implemented)")
                exit_button = QPushButton("Exit")
                exit_button.clicked.connect(self.close)
                button_layout.addWidget(run_tests_button)
                button_layout.addWidget(exit_button)
                layout.addLayout(button_layout)

        if not QApplication.instance():
            app = QApplication(sys.argv)
        else:
            app = QApplication.instance()

        mw = AnkiApp()
        mw.show()
        logger.info("Ankimon Test Environment GUI started.")
        sys.exit(app.exec())

    else:
        AnkiApp()

if __name__ == "__main__":
    main()
