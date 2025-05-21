class PlayerProfile:
    def __init__(self, name):
        self.name = name
        self.inventory = []
        self.clues_found = []

    def add_clue(self, clue):
        self.clues_found.append(clue)

    def add_item(self, item):
        self.inventory.append(item)

