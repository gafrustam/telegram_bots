import random

class GameSession:
    def __init__(self):
        self.level = 1
        self.round = 1
        self.hearts = 3
        self.target_number = ""
        self.current_time = 0.0
        
        # Stats
        self.level_correct_count = 0
        self.max_rounds = 8
        self.state = "IDLE" # IDLE, SHOWING_NUMBER, WAITING_INPUT

    def get_time_for_level(self, level):
        times = {
            1: 15.0, 2: 10.0, 3: 8.0, 4: 6.0, 5: 5.0, 6: 4.0, 
            7: 3.0, 8: 2.5, 9: 2.0, 10: 1.5, 11: 1.25, 12: 1.0
        }
        
        if level in times:
            return times[level]
        else:
            # Level 13 starts at 0.9 (1.0 - 0.1)
            # Formula: 1.0 - ((Level - 12) * 0.1)
            return max(0.1, 1.0 - (level - 12) * 0.1)

    def start_new_round(self):
        """Generates a new number and calculates time limit based on complex rules."""
        self.state = "SHOWING_NUMBER"
        self.target_number = "".join([str(random.randint(0, 9)) for _ in range(6)])
        self.current_time = self.get_time_for_level(self.level)
        return self.target_number, self.current_time

    def check_answer(self, user_input):
        """Returns True if correct, False otherwise. Updates state."""
        self.state = "IDLE"
        if self.target_number and user_input.strip() == self.target_number:
            self.level_correct_count += 1
            self.target_number = "" # Prevent replay
            return True
        else:
            self.hearts -= 1
            return False

    def next_round(self):
        """Advances round or level."""
        self.state = "IDLE"
        self.round += 1
        if self.round > self.max_rounds:
            return "LEVEL_COMPLETE"
        return "NEXT_ROUND"
    
    def advance_level(self):
        self.level += 1
        self.round = 1
        self.level_correct_count = 0
        self.hearts = 3 # Reset hearts on level up? User didn't specify, but usually yes. 
        # Or did they say "3 hearts -- chances to be wrong"? If they pass level, they survive.
        # "After each level completed ... statistics ... Level 3. 4|5 correct"
        # Let's reset rounds.
        return self.level

    def reduce_level(self):
        if self.level > 1:
            self.level -= 1
            self.round = 1
            self.level_correct_count = 0
            # Keep hearts? Or reset? Safer to reset if they engage manual intervention.
            self.hearts = 3 
            return True
        return False

    def increase_level_manual(self):
        self.level += 1
        self.round = 1
        self.level_correct_count = 0
        self.hearts = 3
        return True

    def is_game_over(self):
        return self.hearts <= 0

    def get_formatted_number(self):
        spaced = " ".join(list(self.target_number))
        # Bold the digits
        return f"✨ *{spaced}* ✨"

    def get_hearts_stats(self):
        # Returns string like "❤️ ❤️ 💔" based on current hearts
        # Assuming max hearts is 3
        full = "❤️ " * self.hearts
        broken = "💔 " * (3 - self.hearts)
        return (full + broken).strip()
