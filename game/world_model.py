from enum import Enum

class Unlock_Type(Enum):
    none = 0
    int = 1
    str = 2

shared = []
revealed_items = []

class Item:
    def __init__(self, name, examine_out, unlock_type=Unlock_Type.none, unlock_combination="", examine_reveals=None):
        self.name = name
        self.examine_out = examine_out
        self.examined = False
        self.examine_reveals = examine_reveals or []
        self.unlock_type = unlock_type
        self.unlock_combination = unlock_combination
        self.unlock_attempts = []
        self.unlocked = False

    def examine(self):
        self.examined = True
        for item_name in self.examine_reveals:
            if item_name not in revealed_items:
                revealed_items.append(item_name)
        return self.examine_out

    def unlock(self, combination):
        if combination == self.unlock_combination:
            self.unlocked = True
        else:
            self.unlock_attempts.append(combination)
        return self.unlocked

    def print_item(self):
        ret = f"{self.name}:\n"
        ret += f"  def examine()"
        if self.examined:
            ret += f" = '{self.examine_out}'"
        ret += "\n"

        if self.examined and self.unlock_type != Unlock_Type.none:
            if self.unlocked:
                ret += f"  def unlock({self.unlock_combination}) = True\n"
            else:
                ret += f"  def unlock({self.unlock_type.name})\n"
                for attempt in self.unlock_attempts:
                    ret += f"  unlock({attempt}) = False\n"
        return ret

def share(agent, msg):
    shared.append(f"{agent}: {msg}")

def print_world():
    output = []
    for rev_item_name in revealed_items:
        rev_item = items.get(rev_item_name)
        if rev_item:
            output.append(rev_item.print_item())
    return "\n".join(output)

def load_world_items():
    return items

items = {
    "room": Item("room", "you see a room", examine_reveals=["door", "paper"]),
    "door": Item("door", "the door has a combination lock on it", examine_reveals=["lock"]),
    "paper": Item("paper", "The paper has the number 5871 written on it"),
    "lock": Item("lock", "the lock has a numeric keyboard with 4 spots for digits",
                 unlock_type=Unlock_Type.int, unlock_combination="5871")
}
revealed_items.clear()
revealed_items.append("room")

