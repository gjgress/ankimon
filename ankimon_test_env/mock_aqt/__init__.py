from PyQt6.QtWidgets import QApplication, QMainWindow, QMessageBox
from .reviewer import EnhancedMockReviewer # Expose EnhancedMockReviewer

class MockCollection:
    def __init__(self):
        pass
    # Add more mock methods/attributes as needed, e.g.,
    # def models(self): return MockModels()

class MockMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.col = MockCollection()
        self.setWindowTitle("Ankimon Test Environment")
        self.setGeometry(100, 100, 800, 600)

    def message_box(self, text):
        msg = QMessageBox()
        msg.setText(text)
        msg.exec()

mw = MockMainWindow()
