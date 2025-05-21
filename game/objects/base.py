class GameObject:
    def __init__(self, kind, x, y):
        self.kind = kind
        self.x = x
        self.y = y

    def to_dict(self):
        return {"kind": self.kind, "x": self.x, "y": self.y}
