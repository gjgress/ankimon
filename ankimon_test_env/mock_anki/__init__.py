# mock_anki/__init__.py
from .collection import Collection

class Card:
    def __init__(self, id, question, answer):
        self.id = id
        self.question = question
        self.answer = answer
        print(f"MockCard initialized: {self.id}")

class AnkiUtils:
    def __init__(self):
        print("MockAnkiUtils initialized.")
    def is_win(self):
        print("MockAnkiUtils: is_win called.")
        return True # Assuming Windows for testing based on user's OS
    def isWin(self):
        print("MockAnkiUtils: isWin called.")
        return True # Assuming Windows for testing based on user's OS

class BuildInfo:
    def __init__(self):
        print("MockAnkiBuildInfo initialized.")
    def version(self):
        print("MockAnkiBuildInfo: version called.")
        return "2.1.99 (test)"

class ProfileManager:
    def __init__(self):
        print("MockProfileManager initialized.")
    def openProfile(self, profile_name):
        print(f"MockProfileManager: openProfile called for {profile_name}")

class DataHandler:
    def __init__(self):
        print("MockDataHandler initialized.")

class EnemyPokemon:
    def __init__(self):
        print("MockEnemyPokemon initialized.")

class Achievements:
    def __init__(self):
        print("MockAchievements initialized.")
