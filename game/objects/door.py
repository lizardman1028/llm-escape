from game.objects.base import GameObject

class Door(GameObject):
    def __init__(self, x, y, locked=True):
        super().__init__("door", x, y)
        self.locked = locked

    def examine(self):
        return "The door is {}.".format("locked" if self.locked else "unlocked")

    def unlock(self):
        self.locked = False
        return "You hear a click as the door unlocks."
