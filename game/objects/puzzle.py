from game.objects.base import GameObject

class Puzzle(GameObject):
    def __init__(self, x, y, id, solution):
        super().__init__("puzzle", x, y)
        self.id = id
        self.solution = solution
        self.solved = False

    def attempt(self, guess):
        if guess == self.solution:
            self.solved = True
            return f"Puzzle {self.id} solved!"
        return "Incorrect solution."

    def is_solved(self):
        return self.solved