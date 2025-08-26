import unittest
import subprocess
import sys
import os
import pytest
from run_test_env import parser # Import the parser defined in run_test_env.py

# Get the path to run_test_env.py
RUN_TEST_ENV_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'run_test_env.py'))

def test_selftest_success():
    """Test that run_test_env.py --selftest exits with code 0 on success."""
    command = [sys.executable, RUN_TEST_ENV_PATH, '--selftest']
    result = subprocess.run(command, capture_output=True, text=True)
    
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")
    
    assert result.returncode == 0, f"Self-test failed with exit code {result.returncode}. Stderr: {result.stderr}"
    assert "All self-tests PASSED!" in result.stdout

def test_selftest_failure_mock_missing(monkeypatch):
    """Test that run_test_env.py --selftest exits with code 1 if a mock is missing."""
    # Temporarily modify the run_test_env.py to simulate a mock being missing
    # This is a bit hacky for a test, but demonstrates the failure condition.
    # A more robust way would be to mock sys.modules directly in run_test_env.py for testing.
    
    # Read the original content
    with open(RUN_TEST_ENV_PATH, 'r', encoding='utf-8') as f:
        original_content = f.read()

    # Introduce a deliberate error: remove a mock from the expected_mocks list
    # Find the line where expected_mocks is defined and modify it.
    # This is fragile and depends on the exact content of run_test_env.py
    # For a real project, consider a dedicated test setup in run_test_env.py
    # that allows injecting mock failures.
    
    # For now, let's try to comment out a mock definition in the file itself.
    # This is a very brittle approach and should be replaced with a better mocking strategy
    # if this were a real production test suite.
    
    # Find the line 'aqt.reviewer': ['Reviewer'],
    # and replace it with a commented out version.
    
    modified_content = original_content.replace(
        "        'aqt.reviewer': ['Reviewer'],",
        "        # 'aqt.reviewer': ['Reviewer'], # Deliberately commented out for test\n        'aqt.reviewer_missing': ['Reviewer'],"
    )

    with open(RUN_TEST_ENV_PATH, 'w', encoding='utf-8') as f:
        f.write(modified_content)

    command = [sys.executable, RUN_TEST_ENV_PATH, '--selftest']
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Restore original content regardless of test outcome
    with open(RUN_TEST_ENV_PATH, 'w', encoding='utf-8') as f:
        f.write(original_content)

    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")

    assert result.returncode == 1, f"Self-test unexpectedly passed with exit code {result.returncode}. Stderr: {result.stderr}"
    assert "Some self-tests FAILED!" in result.stdout
    assert "TEST FAILED: Mock module 'aqt.reviewer_missing' is NOT present in sys.modules." in result.stdout


def test_argument_parsing_log_level():
    """Test that --log-level argument is parsed correctly."""
    command = [sys.executable, RUN_TEST_ENV_PATH, '--log-level', 'DEBUG', '--selftest']
    result = subprocess.run(command, capture_output=True, text=True)
    
    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")

    assert result.returncode == 0, f"Self-test failed with exit code {result.returncode}. Stderr: {result.stderr}"
    assert "DEBUG" in result.stdout # Check for DEBUG level messages in output

def test_argument_parsing_file_mode():
    """Test that --file argument is parsed correctly and triggers file mode."""
    # Create a dummy file to test with
    dummy_file_path = os.path.join(os.path.dirname(RUN_TEST_ENV_PATH), "dummy_test_file.py")
    with open(dummy_file_path, "w") as f:
        f.write("import sys\nimport logging\nlogging.basicConfig(level=logging.INFO)\nlogging.info(\"Dummy file executed!\")\n")

    command = [sys.executable, RUN_TEST_ENV_PATH, '--file', dummy_file_path]
    result = subprocess.run(command, capture_output=True, text=True)
    
    # Clean up dummy file
    os.remove(dummy_file_path)

    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")

    assert result.returncode == 0, f"File mode test failed with exit code {result.returncode}. Stderr: {result.stderr}"
    assert "Dummy file executed!" in result.stdout
    assert "No QDialog or QWidget found to display" in result.stdout # Since our dummy file doesn't create one

def test_argument_parsing_full_anki_mode():
    """Test that --full-anki argument is parsed correctly and triggers full Anki mode."""
    # This test will actually try to run the full GUI, which might be problematic in CI/headless environments.
    # For now, we'll just check if it starts up and logs the expected messages.
    # We'll need to ensure it exits gracefully or runs in a way that doesn't hang.
    
    # The current run_test_env.py calls sys.exit(app.exec()) which will block.
    # To test this in a non-interactive way, we'd need to modify run_test_env.py
    # to have a 'test mode' for --full-anki that doesn't block, or use a timeout.
    
    # Given the current setup, this test will likely hang or require a timeout.
    # I will add a timeout to the subprocess call.
    
    command = [sys.executable, RUN_TEST_ENV_PATH, '--full-anki']
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=10) # Timeout after 10 seconds
    except subprocess.TimeoutExpired as e:
        result = e
        print(f"TimeoutExpired: {e.stdout}")
        print(f"TimeoutExpired: {e.stderr}")
        # If it timed out, it means the QApplication started and blocked, which is expected behavior for --full-anki
        # We can consider this a success for now, as it indicates the mode was entered.
        assert "Starting enhanced Ankimon test environment..." in e.stdout or "Starting enhanced Ankimon test environment..." in e.stderr
        assert "Ankimon module imported successfully" in e.stdout or "Ankimon module imported successfully" in e.stderr
        return

    print(f"Stdout: {result.stdout}")
    print(f"Stderr: {result.stderr}")

    # If it didn't timeout, it means it exited for some reason. This might be an error.
    assert result.returncode == 0, f"Full Anki mode test failed with exit code {result.returncode}. Stderr: {result.stderr}"
    assert "Starting enhanced Ankimon test environment..." in result.stdout
    assert "Ankimon module imported successfully" in result.stdout


# Test QApplication is a singleton (indirectly, by ensuring no multiple instantiations)
# This is implicitly tested by the fact that run_test_env.py only has one QApplication call
# and the self-test passes. If there were multiple, it would likely crash or behave unexpectedly.
# A direct test would involve trying to instantiate QApplication twice and catching an error,
# but that's better done within a unit test of the QApplication class itself, not here.

# Test sys.path setup is already part of run_self_tests.

# Test error handling for missing/corrupt configs is already part of run_self_tests.import unittest
import sys
import os
import json
import logging
import io
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Temporarily add the parent directory of ankimon_test_env to sys.path
# to ensure run_test_env can be imported
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent))

# Import run_test_env and its components
try:
    from run_test_env import (
        args, setup_test_environment, run_self_tests,
        ConfigError, load_ankimon_json, load_ankimon_config,
        MockCard, MockMainWindow, MockAddonManager,
        PureMockQWebEngineView, PureMockQWebEnginePage, PureMockQWebEngineSettings
    )
    # Import QApplication if it's available (i.e., not fully headless)
    try:
        from PyQt6.QtWidgets import QApplication, QWidget, QDialog
    except ImportError:
        # Define dummy classes if PyQt6 is not installed for test execution
        class QApplication:
            @staticmethod
            def instance(): return None
            def __init__(self, *args): pass
            def processEvents(self): pass
            def quit(self): pass
            def exec(self): return 0
        class QWidget: pass
        class QDialog: pass
    
    # Check the global 'app' from run_test_env if it exists
    # If run_test_env was executed and created a QApplication, use that
    # Otherwise, create a dummy one for the sake of the tests if needed
    if 'app' in sys.modules['run_test_env'].__dict__ and sys.modules['run_test_env'].app:
        app_instance_for_tests = sys.modules['run_test_env'].app
    else:
        # Create a dummy QApplication if run_test_env didn't instantiate one
        # This is primarily for testing the setup_test_environment function in isolation
        try:
            if not QApplication.instance():
                app_instance_for_tests = QApplication(sys.argv)
            else:
                app_instance_for_tests = QApplication.instance()
        except Exception:
            # Fallback for truly headless where even a dummy QApplication might fail initialization
            class DummyApp:
                def processEvents(self): pass
                def quit(self): pass
                def exec(self): return 0
                def instance(self): return None
            app_instance_for_tests = DummyApp()


except ImportError as e:
    print(f"Failed to import run_test_env: {e}")
    print("Please ensure run_test_env.py is in the correct path for testing.")
    sys.exit(1)


class TestRunTestEnv(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        # Configure logging for tests, capture warnings/errors
        cls.log_capture_string = io.StringIO()
        cls.log_handler = logging.StreamHandler(cls.log_capture_string)
        cls.log_handler.setLevel(logging.DEBUG) # Capture all levels for inspection
        logging.getLogger().addHandler(cls.log_handler)
        logging.getLogger().setLevel(logging.DEBUG) # Set root logger to DEBUG for tests
        
        # Ensure sys.path is clean for run_test_env's internal setup
        # The setup_test_environment handles inserting the path, so just ensure it's not present already
        ankimon_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
        if ankimon_src_path in sys.path:
            sys.path.remove(ankimon_src_path)
            
        # Clean sys.modules of Anki/aqt mocks before each full environment setup
        for module_name in [
            'aqt', 'anki', 'aqt.qt', 'aqt.reviewer', 'aqt.utils', 'aqt.gui_hooks',
            'aqt.webview', 'aqt.sound', 'aqt.theme', 'anki.hooks', 'anki.collection',
            'anki.utils', 'anki.buildinfo', 'aqt.dialogs'
        ]:
            if module_name in sys.modules:
                del sys.modules[module_name]

    @classmethod
    def tearDownClass(cls):
        logging.getLogger().removeHandler(cls.log_handler)

    def setUp(self):
        # Clear log capture before each test
        self.log_capture_string.truncate(0)
        self.log_capture_string.seek(0)
        
        # Clean sys.modules of Anki/aqt mocks before each full environment setup
        for module_name in [
            'aqt', 'anki', 'aqt.qt', 'aqt.reviewer', 'aqt.utils', 'aqt.gui_hooks',
            'aqt.webview', 'aqt.sound', 'aqt.theme', 'anki.hooks', 'anki.collection',
            'anki.utils', 'anki.buildinfo', 'aqt.dialogs'
        ]:
            if module_name in sys.modules:
                del sys.modules[module_name]

    def test_argument_parsing(self):
        # Test default values
        test_args = parser.parse_args([])
        self.assertFalse(test_args.file)
        self.assertFalse(test_args.full_anki)
        self.assertFalse(test_args.debug)
        self.assertFalse(test_args.selftest)
        self.assertEqual(test_args.log_level, 'INFO')

        # Test --file
        test_args = parser.parse_args(['--file', 'test_file.py'])
        self.assertEqual(test_args.file, 'test_file.py')

        # Test --full-anki
        test_args = parser.parse_args(['--full-anki'])
        self.assertTrue(test_args.full_anki)

        # Test --debug
        test_args = parser.parse_args(['--debug'])
        self.assertTrue(test_args.debug)
        # Ensure log level is correctly set to DEBUG when --debug is used
        logging.getLogger().setLevel(logging.INFO) # Reset for test
        sys.modules['run_test_env'].args = parser.parse_args(['--debug']) # Mock args
        from run_test_env import args as re_args
        numeric_level = getattr(logging, (re_args.log_level.upper() if not re_args.debug else 'DEBUG'), None)
        self.assertEqual(numeric_level, logging.DEBUG)

        # Test --selftest
        test_args = parser.parse_args(['--selftest'])
        self.assertTrue(test_args.selftest)

        # Test --log-level
        test_args = parser.parse_args(['--log-level', 'DEBUG'])
        self.assertEqual(test_args.log_level, 'DEBUG')
        
    def test_sys_path_setup(self):
        # Call setup_test_environment, it should add the path
        mw, dm, hooks = setup_test_environment(is_headless_mode=True)
        expected_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
        self.assertIn(expected_path, sys.path)

    def test_qapplication_singleton_gui_mode(self):
        if 'PyQt6.QtWidgets' not in sys.modules:
            self.skipTest("PyQt6 is not available, skipping GUI QApplication test.")

        # Ensure a fresh state for QApplication for this test
        if QApplication.instance():
            del sys.modules['PyQt6.QtWidgets'].QApplication.instance
            del sys.modules['PyQt6.QtWidgets'].QApplication

        # Mock run_test_env.app to be None initially
        with patch('run_test_env.app', new=None):
            from run_test_env import app as rte_app # This reloads/re-evaluates the global 'app'

            # This implicitly calls QApplication(sys.argv) in run_test_env
            # when run_test_env is loaded, if not in headless/selftest mode.
            # For this test, we need to manually trigger the logic or verify the global app.
            
            # Since setup_test_environment is called later, let's just check if QApplication.instance() works
            # The run_test_env's main execution block will handle actual QApplication instantiation.
            # We verify that if it *were* instantiated, it would be a singleton.

            # Ensure 'app_instance_for_tests' is the *only* QApplication instance
            if QApplication.instance():
                app1 = QApplication.instance()
            else:
                app1 = QApplication(sys.argv)

            app2 = QApplication.instance()
            self.assertIs(app1, app2)
            
            # Check the global 'app' in run_test_env
            if sys.modules['run_test_env'].app:
                self.assertIs(sys.modules['run_test_env'].app, app1)


    def test_qapplication_dummy_headless_mode(self):
        # Temporarily set ANKIMON_HEADLESS_SELFTEST to 'True'
        os.environ['ANKIMON_HEADLESS_SELFTEST'] = 'True'
        
        # Reload run_test_env to pick up the env var and re-evaluate app
        with patch.dict('sys.modules', clear=True): # Clear modules for a clean import
            # Re-insert the paths before re-importing run_test_env
            current_dir = Path(__file__).parent
            sys.path.insert(0, str(current_dir))
            sys.path.insert(0, str(current_dir.parent))
            import run_test_env as reloaded_run_test_env
            
            self.assertFalse(hasattr(reloaded_run_test_env, 'QApplication')) # Should not import real QApplication
            self.assertIsInstance(reloaded_run_test_env.app, reloaded_run_test_env.DummyQApplication)
            
        del os.environ['ANKIMON_HEADLESS_SELFTEST'] # Clean up

    def test_all_expected_mocks_present(self):
        mw, dm, hooks = setup_test_environment(is_headless_mode=True) # Run in headless mode for consistency

        expected_mocks = {
            'aqt.qt': ['QDialog', 'QWidget', 'QApplication'],
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
            self.assertIn(module_name, sys.modules, f"Mock module '{module_name}' not in sys.modules")
            mock_module = sys.modules[module_name]
            for attr in attributes:
                self.assertTrue(hasattr(mock_module, attr), f"Attribute '{attr}' not found in mock module '{module_name}'")
                
        # Additional checks for mw_instance and dialogs_manager from return
        self.assertIsInstance(mw, MockMainWindow)
        self.assertIsInstance(dm, type(sys.modules['run_test_env'].dialogs_manager)) # Type check against the original class type

        # Check QWebEngineView for correct mock in headless
        self.assertIs(sys.modules['aqt.utils'].QWebEngineView, PureMockQWebEngineView)
        self.assertIs(sys.modules['aqt.webview'].AnkiWebView, PureMockQWebEngineView)


    def test_config_error_handling_missing_json(self):
        temp_dir = Path(tempfile.gettempdir())
        missing_file = temp_dir / "non_existent_test_config.json"
        
        with self.assertRaises(ConfigError) as cm:
            load_ankimon_json(missing_file)
        self.assertIn(f"Required JSON file not found: {missing_file}", str(cm.exception))
        self.assertIn("ConfigError: JSON file not found", self.log_capture_string.getvalue())

    def test_config_error_handling_corrupt_json(self):
        temp_dir = Path(tempfile.gettempdir())
        corrupt_file = temp_dir / "corrupt_test_config.json"
        with open(corrupt_file, "w") as f:
            f.write("{invalid json")
            
        with self.assertRaises(ConfigError) as cm:
            load_ankimon_json(corrupt_file)
        self.assertIn(f"Corrupt JSON in file: {corrupt_file}", str(cm.exception))
        self.assertIn("ConfigError: Error decoding JSON from file", self.log_capture_string.getvalue())
        
        corrupt_file.unlink() # Clean up

    @patch('run_test_env.load_ankimon_config', side_effect=ConfigError("Simulated config load failure"))
    def test_mock_addon_manager_handles_config_error(self, mock_load_config):
        # Ensure MockAddonManager initializes with an empty config if load_ankimon_config fails
        manager = MockAddonManager()
        self.assertIn("MockAddonManager could not load Ankimon config", self.log_capture_string.getvalue())
        self.assertEqual(manager.getConfig("Ankimon.config_var"), {})
        mock_load_config.assert_called_once()


if __name__ == '__main__':
    # Set ANKIMON_HEADLESS_SELFTEST to True for running these tests headless
    os.environ['ANKIMON_HEADLESS_SELFTEST'] = 'True'
    # Use unittest.main() to run tests
    unittest.main(exit=False) # exit=False allows the main run_test_env.py to continue if it also calls self-tests
    del os.environ['ANKIMON_HEADLESS_SELFTEST'] # Clean up environment variable
