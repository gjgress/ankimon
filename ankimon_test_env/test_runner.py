import sys
import os
import subprocess
import threading
import ast
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QListWidgetItem, QTextEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QListWidget, QWidget
from PyQt6.QtGui import QColor, QAction

ANKIMON_TESTS_DIR = "ankimon_test_env/tests/"
TEST_FILE_PATTERN = "*.py"

class TestRunnerThread(QThread):
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(str, bool, str)

    def __init__(self, test_file_path, test_name):
        super().__init__()
        self.test_file_path = test_file_path
        self.test_name = test_name
        self._is_running = True
        self.docstring = "No docstring found."

    def run(self):
        self.output_signal.emit(f"--- Running test: {self.test_name} ---\\n")
        try:
            try:
                with open(self.test_file_path, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read())
                    doc = ast.get_docstring(tree)
                    if doc:
                        self.docstring = doc
            except Exception as e:
                self.docstring = f"Error parsing docstring: {e}"

            python_executable = sys.executable
            process = subprocess.Popen(
                [python_executable, str(self.test_file_path)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8'
            )

            while self._is_running:
                if process.poll() is not None:
                    break
                self.msleep(50)

            if not self._is_running:
                process.terminate()
                process.wait()
                self.output_signal.emit("\\n--- Test stopped by user ---\\n")
                self.finished_signal.emit(self.test_name, False, self.docstring)
                return

            stdout, stderr = process.communicate()
            if stdout:
                self.output_signal.emit(stdout)
            if stderr:
                self.output_signal.emit(f"ERROR: {stderr}")

            if process.returncode == 0:
                self.output_signal.emit(f"\\n--- Test '{self.test_name}' PASSED ---\\n")
                self.finished_signal.emit(self.test_name, True, self.docstring)
            else:
                self.output_signal.emit(f"\\n--- Test '{self.test_name}' FAILED (Exit code: {process.returncode}) ---\\n")
                self.finished_signal.emit(self.test_name, False, self.docstring)

        except Exception as e:
            self.output_signal.emit(f"ERROR: An unexpected error occurred: {e}")
            self.finished_signal.emit(self.test_name, False, self.docstring)

    def stop(self):
        self._is_running = False

class TestRunnerGUI(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_test_thread = None
        self.test_status = {}
        self.init_ui()
        self.discover_tests()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_panel.setFixedWidth(350)

        self.test_list_widget = QListWidget()
        self.test_list_widget.itemDoubleClicked.connect(self.run_selected_test)

        self.run_button = QPushButton("Run Selected Test")
        self.run_button.clicked.connect(self.run_selected_test)

        self.stop_button = QPushButton("Stop Running Test")
        self.stop_button.clicked.connect(self.stop_current_test)
        self.stop_button.setEnabled(False)

        left_layout.addWidget(QLabel("Available Tests:"))
        left_layout.addWidget(self.test_list_widget)
        left_layout.addWidget(self.run_button)
        left_layout.addWidget(self.stop_button)

        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)

        self.log_output_area = QTextEdit()
        self.log_output_area.setReadOnly(True)

        right_layout.addWidget(QLabel("Test Output:"))
        right_layout.addWidget(self.log_output_area)

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel)

    def discover_tests(self):
        self.test_list_widget.clear()
        test_dir = Path(ANKIMON_TESTS_DIR)
        if not test_dir.is_dir():
            return

        for test_file in sorted(test_dir.glob(TEST_FILE_PATTERN)):
            item = QListWidgetItem(test_file.name)
            item.setData(Qt.ItemDataRole.UserRole, str(test_file.resolve()))
            self.test_list_widget.addItem(item)
            self.test_status[test_file.name] = "Not Run"

    def run_selected_test(self):
        selected_items = self.test_list_widget.selectedItems()
        if not selected_items or (self.current_test_thread and self.current_test_thread.isRunning()):
            return

        item = selected_items[0]
        test_name = item.text()
        test_path = item.data(Qt.ItemDataRole.UserRole)

        self.log_output_area.clear()
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        item.setBackground(QColor("transparent"))

        self.current_test_thread = TestRunnerThread(test_path, test_name)
        self.current_test_thread.output_signal.connect(self.log_output_area.append)
        self.current_test_thread.finished_signal.connect(self.on_test_finished)
        self.current_test_thread.start()

    def stop_current_test(self):
        if self.current_test_thread and self.current_test_thread.isRunning():
            self.current_test_thread.stop()
            self.stop_button.setEnabled(False)

    def on_test_finished(self, test_name, success, docstring):
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.current_test_thread = None

        for i in range(self.test_list_widget.count()):
            item = self.test_list_widget.item(i)
            if item.text() == test_name:
                item.setBackground(QColor("#d4edda" if success else "#f8d7da"))
                item.setToolTip(docstring)
                break