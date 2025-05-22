from game.objects.base import GameObject

class FileCabinet(GameObject):
    def __init__(self, x, y, drawer_contents=None, locked_drawers=None):
        super().__init__("cabinet", x, y)
        self.drawers = drawer_contents if drawer_contents else {}
        self.locked_drawers = locked_drawers if locked_drawers else {}

    def open_drawer(self, n):
        if n not in self.drawers:
            return f"Drawer {n} not found."
        if self.locked_drawers.get(n, False):
            return f"Drawer {n} is locked."
        return self.drawers[n]

    def unlock_drawer(self, n):
        if n in self.locked_drawers:
            self.locked_drawers[n] = False
            return f"Drawer {n} is now unlocked."
        return "Nothing to unlock."
