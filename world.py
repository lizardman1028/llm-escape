import curses
import pygame
# from game.engine import GameEngine
from curses import wrapper
import time
import ollama
from pygame_object import PygameObject
from our_enums import Unlock_Type, Agent_Type, Item_Type
from config import SCREEN_WIDTH, SCREEN_HEIGHT
# from world import World

INITIAL_PROMPT = "Hi! Your name is {}. You are in an escape room! This escape room is specified through a series of Python Objects, and you can interact with the world in this way. To win you need to open the door.\
Here are the objects in the room and their associated functions, the room will update as you interact with it. For your response, you may ONLY respond with a single python function call present in the API.\n Your response is ONE line of python annotated with markdown ```python obj.examine() ```. You may not try multiple functions.\n"

shared = []

revealed_items = []

class Agent:
  name : str
  agent_type : Agent_Type
  revealed_items : list[str] = []
  # world: World
  def __init__(self, name, revealed_items):
    self.name = name
    self.revealed_items = revealed_items

  def turn(self):
    raise NotImplementedError("Interface does not implement turn function")
  
class Item:
  name : str = ""
  examine_out : str = ""
  examined : bool = False
  examined_by : list[str]
  examine_reveals : list[str] 
  unlock_type : Unlock_Type = Unlock_Type.none
  unlock_combination : str = ""
  unlock_attempts : list = []
  unlock_reveals : list[str]
  unlocked : bool = False
  pygame_object : PygameObject = PygameObject((0,0,0),0,0,0,0)
  item_type: Item_Type = Item_Type.ITEM
  def __init__(self, name : str, examine_out : str, unlock_type : Unlock_Type = Unlock_Type.none, unlock_combination : str ="", examine_reveals : list[str] = [], pygame_object : PygameObject = PygameObject((0,0,0), 0,0,0,0), item_type: Item_Type = Item_Type.ITEM, unlock_reveals : list[str] = []):
    self.name = name
    self.examine_out = examine_out
    self.unlock_type = unlock_type
    self.unlock_combination = unlock_combination
    self.examine_reveals = examine_reveals
    self.unlock_reveals = unlock_reveals
    self.item_type = item_type
    self.pygame_object = pygame_object
    self.pygame_object.item_type = item_type
    self.examined = False
    self.unlock_attempts = []
    self.unlocked = False
    self.examined_by = []

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
  def examine(self, agent: Agent):
    self.examined = True
    for item_name in self.examine_reveals:
        if item_name not in agent.revealed_items:
            agent.revealed_items.append(item_name)
    self.examined_by.append(agent.name)
    if agent.agent_type == Agent_Type.LLM:
        return f"{self.name}.examine() = {self.examine_out}"
    return self.examine_out
  def unlock(self, combination, agent: Agent):
    # Accept both "1234" and 1234
    if isinstance(combination, str) and combination.startswith('"') and combination.endswith('"'):
        combination = combination[1:-1]
    combo_str = str(combination).strip()
    target_str = str(self.unlock_combination).strip()
    if combo_str == target_str:
        self.unlocked = True
        for item_name in self.unlock_reveals:
          if item_name not in agent.revealed_items:
              agent.revealed_items.append(item_name)
        # agent.revealed_items.extend(self.unlock_reveals)
        return True
    self.unlock_attempts.append(combo_str)
    return False

class World:
  items : dict[str, Item]
  agent1 : Agent
  agent2 : Agent
  def __init__(self, items):
    self.items = items
    pygame.init()
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Escape Room: Human and LLM")

    self.clock = pygame.time.Clock()
    # Python types are weird, set this manually during 
    # self.engine = GameEngine(self.screen) 
  def start(self):
    while True:
        self.agent1.turn()
        self.agent2.turn()

class CLI_Agent(Agent):
  def __init__(self, name, revealed_items, world):
    self.name = name
    self.revealed_items = revealed_items
    self.world = world
    self.agent_type = Agent_Type.CLI
  
  def turn(self):
    self.render_world()
    print(f"{self.name}>", end="")
    
    user_action = input()
    execute_command(self, user_action)
   

  def render_world(self):
    for rev_item_name in self.revealed_items:
      rev_item = self.world.items.get(rev_item_name, None)
      if rev_item == None:
        continue
      print(rev_item.print_item(), end="")

class LLM_Agent(Agent):
  messages = []
  model : str
  initial_prompt : bool = True
  last_action_res : str
  x : int
  y : int
  
  def __init__(self, name, revealed_items, model='deepseek-r1:32b', world: World=World({})):
    self.name = name
    self.world = world
    self.revealed_items = revealed_items
    self.model = model
    self.agent_type = Agent_Type.LLM
    self.last_action_res = ""
    self.is_thinking = False
    self.x = int(world.items[revealed_items[0]].pygame_object.center_x)
    self.y = int(world.items[revealed_items[0]].pygame_object.center_y)

  def create_prompt(self):
    prompt = ""
    if self.initial_prompt:
      prompt += INITIAL_PROMPT.format(self.name)
      #TODO: Uncomment self.initial_prompt = False
      self.initial_prompt = False
    else:
      prompt += self.last_action_res
    for rev_item_name in self.revealed_items:
      rev_item = self.world.items.get(rev_item_name, None)
      if rev_item == None:
        continue
      prompt += rev_item.print_item()
    return prompt
  
  def render_prompt(self, prompt):
    print(prompt, end="")
  
  def turn(self):
    prompt = self.create_prompt()
    #TODO: remove following line:
    # self.messages = []
    self.messages.append({
      'role': 'user',
      'content': prompt,
    })
    stream = ollama.chat(
      model='deepseek-r1:32b', 
      messages=self.messages, 
      stream=True
    )

    response = ""
    
    self.render_prompt(prompt)
    done_thinking = False
    self.is_thinking = True
    print("Thinking", end="", flush=True)
    for chunk in stream:
      part = chunk['message']['content']
      response = response + part
      if response.find("</think>") != -1:
        done_thinking = True
        self.is_thinking = False
      if done_thinking:
        print(part, end="")
      else:
        print(".", end="", flush=True)
        self.world.engine.old_draw_agent_view(self)
        pygame.display.flip()
        # agent.world.clock.tick(60)
    
    self.messages.append({
      'role': 'assistant',
      'content': response,
    })

    python_start = response.find("```python")
    python_start += 10
    python_end = response[python_start:].find("```")
    python_instr = response[python_start:][:python_end]
    print("\n", end="")
    print(self.name + ">", end="")
    print(python_instr, end="")

    cmd = python_instr
    
    execute_command(self, cmd)

  def get_room(self) -> Item:
        item_obj = None
        for item_name in self.revealed_items:
            # print(f"item_name:{item_name}")
            item_obj = self.world.items.get(item_name)
            if item_obj == None:
                continue
            if item_obj.item_type != Item_Type.ROOM:
                # print(f"item_obj{item_obj}")
                continue
            if item_obj.pygame_object.player_inside(self.x, self.y):
                # print("In Room!")
                return item_obj
        return Item("","")


# def print_world():
#   for rev_item_name in revealed_items:
#     rev_item = self.world.items.get(rev_item_name, None)
#     if rev_item == None:
#       continue
#     # print(rev_item.print_item())
#     print(rev_item.print_item(), end="")

# def print_agent_world(agent: Agent):
#   for rev_item_name in agent.revealed_items:
#     rev_item = agent.world.items.get(rev_item_name, None)
#     if rev_item == None:
#       continue
#     # print(rev_item.print_item())
#     print(rev_item.print_item(), end="")

# class Item:
#   name : str = ""
#   examine_out : str = ""
#   examined : bool = False
#   examine_reveals : list[str] 
#   unlock_type : Unlock_Type = Unlock_Type.none
#   unlock_combination : str = ""
#   unlock_attempts : list = []
#   unlocked : bool = False
#   pygame_object : PygameObject = PygameObject((0,0,0),0,0,0,0)
#   item_type: Item_Type = Item_Type.ITEM
#   def __init__(self, name : str, examine_out : str, unlock_type : Unlock_Type = Unlock_Type.none, unlock_combination : str ="", examine_reveals : list[str] = [], pygame_object : PygameObject = PygameObject((0,0,0), 0,0,0,0), item_type: Item_Type = Item_Type.ITEM):
#     self.name = name
#     self.examine_out = examine_out
#     self.unlock_type = unlock_type
#     self.unlock_combination = unlock_combination
#     self.examine_reveals = examine_reveals
    
#     self.item_type = Item_Type.ITEM
#     self.pygame_object = pygame_object
#     self.pygame_object.item_type = Item_Type.ITEM
#     self.examined = False
#     self.unlock_attempts = []
#     self.unlocked = False

#   def print_item(self):
#     ret = ""
#     ret += f"{self.name}:\n"
#     ret += f"  def examine()"
#     if (self.examined):
#       ret += f" = '{self.examine_out}'"
#     ret += "\n"
#     if (self.examined):
#       if (self.unlock_type == Unlock_Type.none):
#         ret += ""
#       if (self.unlock_type == Unlock_Type.int or self.unlock_type == Unlock_Type.str):
#         if self.unlocked:
#           ret += f"  def unlock({self.unlock_combination}) = True\n"
#         else:
#           ret += f"  def unlock({self.unlock_type.name})\n"
#         if (len(self.unlock_attempts) > 0 and not self.unlocked):
#           for attempt in self.unlock_attempts:
#             ret += f"  unlock({attempt}) = False\n"
#     return ret
#   def examine(self, agent : Agent):
#     self.examined = True
#     for item_name in self.examine_reveals:
#       agent.revealed_items.append(item_name)
#     if agent.agent_type == Agent_Type.LLM:
#       return f"{self.name}.examine() = {self.examine_out}"
#     return self.examine_out
#   def unlock(self, combination):
#     if combination == self.unlock_combination:
#       self.unlocked = True
#     else:
#       self.unlock_attempts.append(combination)
#     return combination == self.unlock_combination

def share(agent : Agent, msg):
  shared.append(f"{agent.name}: {msg}")

def execute_command(agent, cmd):
  print(f"[exec] cmd = {cmd}")
  print(f"[exec] agent revealed_items = {agent.revealed_items}")
  dot_ind = cmd.find('.')
  open_ind = cmd.find('(')
  close_ind = cmd.find(')')
  if dot_ind == -1 or open_ind == -1 or close_ind == -1:
    print("Function not found\n", end="")
    return agent.turn()
  pre_dot = cmd[:dot_ind]
  post_dot = cmd[dot_ind:]
  cur_item = agent.world.items.get(pre_dot, None)
  # if cur_item == None or pre_dot not in agent.revealed_items:
  #   print("Item not found\n", end="")
  #   return agent.turn()
  if not isinstance(cur_item, Item): # this variation allows examine for nearby unrevealed items
    return "Item not found"
  
  if agent.agent_type == Agent_Type.LLM:
    desired_x = cur_item.pygame_object.center_x
    desired_y = cur_item.pygame_object.center_y
    x_displ = desired_x - agent.x
    y_displ = desired_y - agent.y
    x_displ_per_frame = x_displ/20
    y_displ_per_frame = y_displ/20
    for frame in range(0,20):
      agent.x += x_displ_per_frame
      agent.y += y_displ_per_frame
      agent.world.engine.old_draw_agent_view(agent)
      pygame.display.flip()
      agent.world.clock.tick(60)



  if post_dot.startswith(".examine("):
    result = cur_item.examine(agent)
    if agent.world.agent1.name != agent.name and agent.get_room().name == agent.world.agent1.get_room().name:
      cur_item.examine(agent.world.agent1)
    if agent.world.agent2.name != agent.name and agent.get_room().name == agent.world.agent2.get_room().name:
      cur_item.examine(agent.world.agent2)
    # if agent.world.agent1.name != agent.name:
    #   cur_item.examine(agent.world.agent1)
    return result
  if pre_dot not in agent.revealed_items:
    return "Item not revealed"
  if post_dot.startswith(".examine("):
    # print(cur_item.name, end="")
    print(f"[exec] calling examine on {pre_dot}")

    

    return cur_item.examine(agent)
  if post_dot.startswith(".unlock("):
    cur_combo = post_dot[8:post_dot.find(')')]
    print(f"[exec] trying unlock({cur_combo}) on {pre_dot}")
    success = cur_item.unlock(cur_combo, agent=agent)
    if success:
      if agent.world.agent1.name != agent.name and agent.get_room().name == agent.world.agent1.get_room().name:
          cur_item.unlock(cur_combo, agent.world.agent1)
      if agent.world.agent2.name != agent.name and agent.get_room().name == agent.world.agent2.get_room().name:
          cur_item.unlock(cur_combo, agent.world.agent2)
    return "Unlocked!" if success else "Incorrect combination"
  return "No valid API matched"


# items = {
#   "room":Item("room", "you see a room, you see a door on the wall, and a piece of paper on the ground", examine_reveals=["door", "paper"]), 
#   "paper":Item("paper", "The paper has the number 5871 written on it"),
#   "lock":Item("door", "the door has a combination lock on it, the lock has a numeric keyboard with 4 spots for digits", unlock_type=Unlock_Type.int, unlock_combination="5871")}
# revealed_items = ["room"]

# cli_agent =  CLI_Agent("Cli Agent", ["room"])
# llm_agent = LLM_Agent("LLM_Agent", ["room"])


# while True:
#   # cli_agent.turn()
#   llm_agent.turn()
#   time.sleep(1)