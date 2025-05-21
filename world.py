from enum import Enum

class Unlock_Type(Enum):
  none = 0
  int = 1
  str = 2

shared = []

revealed_items = []

class item:
  name : str = ""
  examine_out : str = ""
  examined : bool = False
  examine_reveals : list[str] 
  unlock_type : Unlock_Type = Unlock_Type.none
  unlock_combination : str = ""
  unlock_attempts : list = []
  unlocked : bool = False
  def __init__(self, name, examine_out, unlock_type=Unlock_Type.none, unlock_combination="", examine_reveals=[]):
    self.name = name
    self.examine_out = examine_out
    self.unlock_type = unlock_type
    self.unlock_combination = unlock_combination
    self.examine_reveals = examine_reveals
  def print_item(self):
    ret = ""
    ret += f"{self.name}:\n"
    ret += f"  def examine()"
    if (self.examined):
      ret += f" = '{self.examine_out}'"
    ret += "\n"
    if (self.examined):
      if (self.unlock_type == Unlock_Type.none):
        ret += ""
      if (self.unlock_type == Unlock_Type.int or self.unlock_type == Unlock_Type.str):
        if self.unlocked:
          ret += f"  def unlock({self.unlock_combination}) = True\n"
        else:
          ret += f"  def unlock({self.unlock_type.name})\n"
        if (len(self.unlock_attempts) > 0 and not self.unlocked):
          for attempt in self.unlock_attempts:
            ret += f"  unlock({attempt}) = False\n"
    return ret
  def examine(self):
    self.examined = True
    for item_name in self.examine_reveals:
      revealed_items.append(item_name)
    return self.examine_out
  def unlock(self, combination):
    if combination == self.unlock_combination:
      self.unlocked = True
    else:
      self.unlock_attempts.append(combination)
    return combination == self.unlock_combination

def share(agent, msg):
  shared.append(f"{agent}: {msg}")

def print_world():
  for rev_item_name in revealed_items:
    rev_item = items.get(rev_item_name, None)
    if rev_item == None:
      continue
    print(rev_item.print_item())

items = {
  "room":item("room", "you see a room", examine_reveals=["door", "paper"]), 
  "door":item("door", "the door has a combination lock on it", examine_reveals=["lock"]),
  "paper":item("paper", "The paper has the number 5871 written on it"),
  "lock":item("lock", "the lock has a numeric keyboard with 4 spots for digits", unlock_type=Unlock_Type.int, unlock_combination="5871")}
revealed_items = ["room"]

while True:
  print_world()
  user_action = input(">")
  dot_ind = user_action.find('.')
  open_ind = user_action.find('(')
  close_ind = user_action.find('(')
  if dot_ind == -1 or open_ind == -1 or close_ind == -1:
    print("Function not found")
    continue
  pre_dot = user_action[:dot_ind]
  post_dot = user_action[dot_ind:]
  cur_item = items.get(pre_dot, None)
  if cur_item == None or pre_dot not in revealed_items:
    print("Item not found")
    continue
  if post_dot == ".examine()":
    cur_item.examine()
  if post_dot.find(".unlock(") == 0:
    cur_combo = post_dot[8:-1]
    cur_item.unlock(cur_combo)
  
