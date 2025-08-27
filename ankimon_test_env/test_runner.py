import sys
import os
import subprocess
import threading
from pathlib import Path
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import QListWidgetItem, QTextEdit, QPushButton, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy, QListWidget
from PyQt6.QtGui import QColor

# --- Test Runner Configuration ---
ANKIMON_TESTS_DIR = "ankimon_test_env/tests/"
TEST_FILE_PATTERN = "*.py"

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

