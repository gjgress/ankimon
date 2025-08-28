# mock anki.collection

class MockNote:
    def __init__(self):
        self.id = 456
        self._tags = []

    def has_tag(self, tag):
        return tag in self._tags

class MockCurrentState:
    def __init__(self):
        self.custom_data = {}

class MockSchedulingStates:
    def __init__(self):
        self.current = MockCurrentState()

class MockCard:
    def __init__(self, id: int, question: str, answer: str):
        self.id = id
        self._question = question
        self._answer = answer
        self._note = MockNote()
        self._user_flag = 0
        self._ord = 0 # Card ordinal for template rendering
        self._current_deck_id = 1 # Default deck ID
        self._ivl = 1 # Interval in days
        self._due = 0 # Due date (relative to now)
        self._lapses = 0 # Number of times card has been lapsed
        self._reps = 0 # Number of times card has been reviewed

    def load(self):
        print(f"MockCard {self.id}: Loading card data.")

    def question(self):
        return self._question

    def answer(self):
        return self._answer

    def autoplay(self):
        return False

    def question_av_tags(self):
        return []

    def answer_av_tags(self):
        return []

    def note(self):
        return self._note

    def user_flag(self):
        return self._user_flag

    def note_type(self):
        return {"flds": []} # Placeholder for note type fields

    def current_deck_id(self):
        return self._current_deck_id

    def time_taken(self):
        return 0

    def should_show_timer(self):
        return False

    def time_limit(self):
        return 0

class MockQueuedCard:
    def __init__(self):
        self.card = MockCard(123) # Default mock card
        self.states = MockSchedulingStates()
        self.context = {}
        self.queue = 2 # Simulate review queue

class MockQueuedCards:
    def __init__(self, new_count=0, learning_count=0, review_count=0):
        self.cards = [MockQueuedCard()] # Still keep a dummy card for now
        self.new_count = new_count
        self.learning_count = learning_count
        self.review_count = review_count

class MockProgress:
    def single_shot(self, delay_ms, callback, parent=None):
        print(f"MockProgress: Single shot timer set for {delay_ms}ms with {callback.__name__}")
        # In a real mock, you might want to simulate this delay and call the callback
        callback() # Immediately call for now for simplicity

    def timer(self, interval_ms, callback, repeat=False, parent=None):
        print(f"MockProgress: Timer set for {interval_ms}ms, repeat={repeat} with {callback.__name__}")
        # Simulate immediate call for now
        callback()
        return MockTimer()

class MockTimer:
    def remainingTime(self):
        return 0
    def deleteLater(self):
        print("MockTimer: deleteLater called")

class MockV3CardInfo:
    def __init__(self, card):
        self.queued_cards = MockQueuedCards()
        self.states = MockSchedulingStates()
        self.context = {}
        self.card = card

    def top_card(self):
        return self.queued_cards.cards[0]

    def counts(self):
        return 2, [self.queued_cards.new_count, self.queued_cards.learning_count, self.queued_cards.review_count]

    @staticmethod
    def rating_from_ease(ease: int):
        # Simplified mapping
        if ease == 1: return "AGAIN"
        elif ease == 2: return "HARD"
        elif ease == 3: return "GOOD"
        else: return "EASY"

class MockScheduler:
    def __init__(self, mw_instance):
        self.mw = mw_instance
        self._queue = [
            MockCard(1, "What is 2+2?", "4"),
            MockCard(2, "What is the capital of France?", "Paris"),
            MockCard(3, "What is the largest planet?", "Jupiter"),
            MockCard(4, "What is the smallest prime number?", "2"),
            MockCard(5, "What is the color of the sky?", "Blue"),
        ]
        self.new_count = len(self._queue)
        self.learning_count = 0
        self.review_count = 0
        self.current_card_index = -1

    def get_next_card(self):
        self.current_card_index += 1
        if self.current_card_index < len(self._queue):
            return self._queue[self.current_card_index]
        else:
            print("[MOCK Scheduler] No more cards in the queue.")
            return None

    def startReview(self):
        print("[MOCK Scheduler] startReview() called.")
        # The reviewer's show method will handle getting the first card
        self.mw.reviewer.show()

    def answerButtons(self, card):
        return 4 # Simulate 4 answer buttons

    def describe_next_states(self, states):
        # Placeholder for describing next states
        return ["1m", "10m", "1d", "4d"]

    def answerCard(self, card: MockCard, ease: int):
        print(f"MockScheduler: Answering card {card.id} with ease {ease}")
        card._reps += 1
        if ease == 1: # Again
            card._lapses += 1
            card._ivl = 1
            card._due = 0 # Due immediately
            # Re-add to front of queue for simplicity in mock
            self._queue.insert(0, card)
            self.learning_count += 1
        elif ease == 2: # Hard
            card._ivl = max(1, int(card._ivl * 1.2))
            card._due = card._ivl
            self.learning_count += 1
        elif ease == 3: # Good
            card._ivl = max(1, int(card._ivl * 2.5))
            card._due = card._ivl
            self.review_count += 1
        elif ease == 4: # Easy
            card._ivl = max(1, int(card._ivl * 3.5))
            card._due = card._ivl
            self.review_count += 1
        
        # Remove card from current queue if it was new
        if card in self._queue:
            self._queue.remove(card)
            self.new_count = len(self._queue) # Update new count

        print(f"MockScheduler: Card {card.id} new ivl: {card._ivl}, due: {card._due}")

    def get_next_card(self):
        """Get the next card to review"""
        self.current_card_index += 1
        if self.current_card_index < len(self._queue):
            card = self._queue[self.current_card_index]
            print(f"MockScheduler: Retrieved card {card.id}: {card.question()}")
            return card
        else:
            print("[MOCK Scheduler] No more cards in the queue.")
            return None


class Collection:
    def __init__(self):
        print("Mock anki.Collection initialized.")
        self._notes = []
        self.conf = {} # Initialize config
        self.sched = None 

    def get_config(self, key):
        print(f"Mock anki.Collection: get_config called for {key}")
        return self.conf.get(key)

    def set_config(self, key, value):
        print(f"Mock anki.Collection: set_config called for {key} = {value}")
        self.conf[key] = value

    def add_note(self, note):
        print(f"Mock anki.Collection: add_note called for {note}")
        self._notes.append(note)

    def all_notes(self):
        print("Mock anki.Collection: all_notes called.")
        return self._notes

    def get_card(self, card_id):
        print(f"Mock anki.Collection: Getting card with ID: {card_id}")
        for card in self._cards:
            if card.id == card_id:
                return card
        return None # Card not found

    def sched_ver(self):
        return 3 # Simulate v3 scheduler

    def v3_scheduler(self):
        return True
