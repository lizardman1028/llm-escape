from game.objects.base import GameObject

class FileCabinet(GameObject):
    def __init__(self, x, y):
        super().__init__("cabinet", x, y)
        self.drawers = {
            1: "Empty",
            2: "Paper with clue: 'code = 1234'",
            3: "Locked drawer"
        }
        self.locked_drawers = {3: True}

    def open_drawer(self, n):
        if n not in self.drawers:
            return "Drawer not found."
        if self.locked_drawers.get(n):
            return f"Drawer {n} is locked."
        return self.drawers[n]

    def unlock_drawer(self, n):
        if n in self.locked_drawers:
            self.locked_drawers[n] = False
            return f"Drawer {n} is now unlocked."
        return "Nothing to unlock."
