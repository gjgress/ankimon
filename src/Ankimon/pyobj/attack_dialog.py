from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QScrollArea
from PyQt6.QtCore import Qt

class AttackDialog(QDialog):
    """A dialog for managing a Pokémon's moveset when learning a new attack.

    When a Pokémon attempts to learn a new move but already knows four, this
    dialog is presented to the user, allowing them to choose which existing
    move to replace. This is a crucial component of the Pokémon progression
    system, ensuring that the user has full control over their Pokémon's
    abilities.
    """
    def __init__(self, attacks, new_attack):
        """Initializes the attack selection dialog.

        Args:
            attacks (list): A list of the Pokémon's current attacks.
            new_attack (str): The new attack that the Pokémon is trying to learn.
        """
        super().__init__()
        self.attacks = attacks
        self.new_attack = new_attack
        self.selected_attack = None
        self.initUI()

    def initUI(self):
        """Initializes the user interface of the attack selection dialog."""
        self.setWindowTitle(f"Select which Attack to Replace with {self.new_attack}")
        layout = QVBoxLayout()
        layout.addWidget(QLabel(f"Select which Attack to Replace with {self.new_attack}"))
        for attack in self.attacks:
            button = QPushButton(attack)
            button.clicked.connect(self.attackSelected)
            layout.addWidget(button)
        reject_button = QPushButton("Reject Attack")
        reject_button.clicked.connect(self.attackNoneSelected)
        layout.addWidget(reject_button)
        self.setLayout(layout)

    def attackSelected(self):
        """Handles the selection of an attack to be replaced."""
        sender = self.sender()
        self.selected_attack = sender.text()
        self.accept()

    def attackNoneSelected(self):
        """Handles the rejection of the new attack."""
        sender = self.sender()
        self.selected_attack = sender.text()
        self.reject()