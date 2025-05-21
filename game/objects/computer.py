from game.objects.base import GameObject

class Computer(GameObject):
    def __init__(self, x, y, password="open123"):
        super().__init__("computer", x, y)
        self.password = password
        self.input = ""

    def submit(self, text):
        if text == self.password:
            return "Password accepted. Access granted."
        return "Incorrect password."
