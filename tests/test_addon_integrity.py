import os
import sys
import importlib
import pkgutil
import traceback
import pytest
from unittest.mock import MagicMock

# Import aqt modules BEFORE QApplication is instantiated by pytest-qt.
try:
    import aqt
    import aqt.qt
except ImportError:
    pass

# Add the 'src' directory to the Python path to allow for absolute imports of Ankimon
ANKIMON_SRC_PARENT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src'))
if ANKIMON_SRC_PARENT_DIR not in sys.path:
    sys.path.insert(0, ANKIMON_SRC_PARENT_DIR)

def test_ankimon_initialization(qapp):
    """
    Dynamically loads the Ankimon add-on to catch real AttributeError or ImportError
    that happen at module level, such as failing to register GUI hooks properly.
    `qapp` is a pytest-qt fixture that provides a QApplication instance, allowing
    real PyQt6 widgets to be instantiated without crashing.
    """
    import aqt
    from PyQt6.QtWidgets import QMainWindow

    # Instead of a MagicMock which Qt rejects for parent classes, use a real QWidget
    # as the mock main window.
    class MockMainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.pm = MagicMock()
            self.pm.name = "test_profile"
            self.form = MagicMock()
            self.addonManager = MagicMock()

        def _increase_background_ops(self):
            pass

        def _decrease_background_ops(self):
            pass

    aqt.mw = MockMainWindow()

    # Mocking QThreadPool and query execution because we don't want background threads to actually run in the test
    aqt.mw.taskman = MagicMock()

    # Track errors
    errors = []

    try:
        # Import the main __init__ to simulate Anki loading the add-on
        import Ankimon
    except Exception as e:
        error_msg = f"Failed to load Ankimon/__init__.py:\n{traceback.format_exc()}"
        errors.append(error_msg)

    # Also attempt to dynamically import all submodules within Ankimon
    # to catch any missing functions/attributes in files that might not be directly imported
    import Ankimon
    package = Ankimon
    prefix = package.__name__ + "."

    # The poke_engine/data/scripts are standalone scripts meant to be run directly by
    # node or python individually rather than imported as python packages in Anki.
    ignore_modules = ["pypresence", "Ankimon.poke_engine.data.scripts", "Ankimon.poke_engine.data.mods"]

    for importer, modname, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        if any(ignored in modname for ignored in ignore_modules):
            continue

        try:
            importlib.import_module(modname)
        except Exception as e:
            error_msg = f"Failed to dynamically import module {modname}:\n{traceback.format_exc()}"
            errors.append(error_msg)

    if errors:
        error_text = "\n".join(errors)
        pytest.fail(f"Integrity check failed with {len(errors)} error(s):\n{error_text}")
