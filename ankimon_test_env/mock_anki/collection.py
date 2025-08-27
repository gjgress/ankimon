# mock anki.collection

class Collection:
    def __init__(self):
        print("Mock anki.Collection initialized.")
    def get_config(self, key):
        print(f"Mock anki.Collection: get_config called for {key}")
        return None
    def set_config(self, key, value):
        print(f"Mock anki.Collection: set_config called for {key} = {value}")
    def add_note(self, note):
        print(f"Mock anki.Collection: add_note called for {note}")
    def all_notes(self):
        print("Mock anki.Collection: all_notes called.")
        return []
