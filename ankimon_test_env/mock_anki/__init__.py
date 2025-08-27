# mock_anki/__init__.py

class MockCard:
    def __init__(self, id, question, answer):
        self.id = id
        self.question = question
        self.answer = answer
        print(f"MockCard initialized: {self.id}")

class MockAnkiUtils:
    def __init__(self):
        print("MockAnkiUtils initialized.")
    def is_win(self):
        print("MockAnkiUtils: is_win called.")
        return True # Assuming Windows for testing based on user's OS
    def isWin(self):
        print("MockAnkiUtils: isWin called.")
        return True # Assuming Windows for testing based on user's OS

class MockAnkiBuildInfo:
    def __init__(self):
        print("MockAnkiBuildInfo initialized.")
    def version(self):
        print("MockAnkiBuildInfo: version called.")
        return "2.1.99 (test)"

class MockProfileManager:
    def __init__(self):
        print("MockProfileManager initialized.")
    def openProfile(self, profile_name):
        print(f"MockProfileManager: openProfile called for {profile_name}")

class MockDataHandler:
    def __init__(self):
        print("MockDataHandler initialized.")

class MockEnemyPokemon:
    def __init__(self):
        print("MockEnemyPokemon initialized.")

class MockAchievements:
    def __init__(self):
        print("MockAchievements initialized.")
