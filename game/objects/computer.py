from game.objects.base import GameObject

class Computer(GameObject):
    def __init__(self, x, y, password=None, unlock_target_id=None):
        super().__init__("computer", x, y)
        self.password = password
        self.unlock_target_id = unlock_target_id  # e.g. "exit"

    def submit(self, text, room_objects):
        if text == self.password:
            if self.unlock_target_id:
                for obj in room_objects:
                    if obj.kind == "door" and getattr(obj, "id", None) == self.unlock_target_id:
                        obj.locked = False
                        return "Access granted. The exit door is now unlocked."
            return "Access granted."
        return "Access denied."

