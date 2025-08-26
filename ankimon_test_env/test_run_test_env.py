import subprocess
import sys
import os
import pytest

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
        "        # 'aqt.reviewer': ['Reviewer'], # Deliberately commented out for test
        "aqt.reviewer_missing": ['Reviewer'], # Add a non-existent mock to trigger failure
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

# Test error handling for missing/corrupt configs is already part of run_self_tests.