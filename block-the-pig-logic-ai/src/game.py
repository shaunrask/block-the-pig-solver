import subprocess
import time

class BlockThePigGame:
    def __init__(self):
        self.radius = 4
        self.pig_pos = (0, 0)
        self.walls = set()
        self.escapes = self._generate_escapes()
        self.turn = "PLAYER" # PLAYER (Wall) or PIG

    def _generate_escapes(self):
        escapes = set()
        for q in range(-self.radius, self.radius + 1):
            for r in range(-self.radius, self.radius + 1):
                if -self.radius <= q + r <= self.radius:
                    if abs(q) == self.radius or abs(r) == self.radius or abs(q + r) == self.radius:
                        escapes.add((q, r))
        return escapes

    def print_board(self):
        print(f"Pig at: {self.pig_pos}")
        print(f"Walls at: {self.walls}")
        # Simple text viz could be added here

    def get_player_move(self):
        # In a real game, this would come from UI or Spectra
        # For now, ask user
        try:
            move_str = input("Enter wall coord (q,r): ")
            q, r = map(int, move_str.split(","))
            return (q, r)
        except ValueError:
            return None

    def get_pig_move(self):
        # Simple greedy pig: move towards closest escape
        # Or random
        return self.pig_pos # Placeholder

    def play(self):
        while True:
            self.print_board()
            
            if self.pig_pos in self.escapes:
                print("Pig Escaped! You Lose.")
                break
            
            # Check if trapped (simplified)
            # ...

            if self.turn == "PLAYER":
                move = self.get_player_move()
                if move:
                    if move not in self.walls and move != self.pig_pos:
                        self.walls.add(move)
                        self.turn = "PIG"
                    else:
                        print("Invalid move")
            else:
                # Pig turn
                new_pos = self.get_pig_move()
                self.pig_pos = new_pos
                self.turn = "PLAYER"

if __name__ == "__main__":
    game = BlockThePigGame()
    game.play()
