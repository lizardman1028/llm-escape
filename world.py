import curses
import pygame
# from game.engine import GameEngine
from curses import wrapper
import time
import ollama
from pygame_object import PygameObject
from our_enums import Unlock_Type, Agent_Type, Item_Type
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from enum import Enum
# from world import World

INITIAL_PROMPT = "Hi! Your name is {}. You are in an escape room! This escape room is specified through a series of Python Objects, and you can interact with the world in this way.\
Here are the objects in the room and their associated functions, the room will update as you interact with it. For your response, you may ONLY respond with a single python function call present in the API.\n Your response is ONE line of python annotated with markdown ```python obj.examine() ```. You may not try multiple functions.\n"

INITIAL_PROMPT_MULTI_PLAYER = "Hi! Your name is {}. You are in an escape room with another player {}! This escape room is specified through a series of Python Objects, and you can interact with the world in this way.\
Here are the objects in the room and their associated functions, the room will update as you and your teamate interact with it. For your response, you may ONLY respond with a single python function call present in the API.\n Your response is ONE line of python annotated with markdown ```python obj.examine() ```. You may not try multiple functions.\n"


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
          for attempt in self.unlock_attempts:
              # print(attempt)
              ret += f"  unlock({attempt}) = False\n"
    return ret
  def print_item_func_only(self):
    ret = ""
    # ret += f"{self.name}:\n"
    ret += f"{self.name}.examine()"
    if (self.examined):
      ret += f" = '{self.examine_out}'"
    ret += "\n"
    if (self.examined):
      if (self.unlock_type == Unlock_Type.none):
        ret += ""
      if (self.unlock_type == Unlock_Type.int or self.unlock_type == Unlock_Type.str):
        if self.unlocked:
          ret += f"{self.name}.unlock({self.unlock_combination}) = True\n"
        else:
          ret += f"{self.name}.unlock({self.unlock_type.name})\n"
          for attempt in self.unlock_attempts:
            ret += f"{self.name}.unlock({attempt}) = False\n" 
    return ret

  def examine(self, agent: Agent):
    self.examined = True
    for item_name in self.examine_reveals:
        if item_name not in agent.revealed_items:
            agent.revealed_items.append(item_name)
    self.examined_by.append(agent.name)
    if agent.agent_type == Agent_Type.LLM:
        agent.last_action_res = f"{self.name}.examine() = {self.examine_out}"
        return f"{self.name}.examine() = {self.examine_out}"
    return self.examine_out
  def unlock(self, combination, agent: Agent):
    # Accept both "1234" and 1234
    if isinstance(combination, str) and combination.startswith('"') and combination.endswith('"'):
        combination = combination[1:-1]
    combo_str = str(combination).strip()
    target_str = str(self.unlock_combination).strip()
    self.unlock_attempts.append(combo_str)
    if combo_str == target_str:
        self.unlocked = True
        for item_name in self.unlock_reveals:
          if item_name not in agent.revealed_items:
              agent.revealed_items.append(item_name)
        # agent.revealed_items.extend(self.unlock_reveals)
        if agent.agent_type == Agent_Type.LLM:
          agent.last_action_res = f"{self.name}.unlock({combination}) = True"
        return True
    
    # print(self.unlock_attempts)
    if agent.agent_type == Agent_Type.LLM:
      agent.last_action_res = f"{self.name}.unlock({combination}) = False"
    return False

class World:
  items : dict[str, Item]
  agent1 : Agent
  agent2 : Agent
  shared : list[str]
  def __init__(self, items):
    self.items = items
    pygame.init()
    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Escape Room: Human and LLM")

    self.clock = pygame.time.Clock()
    self.shared = []
    # Python types are weird, set this manually during 
    # self.engine = GameEngine(self.screen) 
  def share(self, agent, str):
    str_to_share = f"{agent.name}: {str}"
    self.shared.append(str_to_share)
  def start(self):
    turns = 0
    while True:
        self.agent1.turn()
        self.agent2.turn()
        turns += 1
        print(f"TURN: {turns}")
        if self.items["room3"].examined:
           print("ROOM ESCAPED")
           break
        if turns > 15:
           print("ROOM FAILED")
           break

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
    self.messages = []
    
    #Formatting Variations
    self.show_last_action = True
    self.header_for_new_state = True
    
    # only_action overrides post_think
    self.remember_only_action = False
    self.remember_only_post_think = True

    self.initial_prompt_multiplayer = True

    self.remember_only_valid = True
    self.remember_only_correct = False

    self.api_funcs_only = False
  def llm_config(self, 
                 api_funcs_only:bool,
                 show_last_action:bool, 
                 header_for_new_state:bool, 
                 
                 remember_only_valid:bool,
                 remember_only_correct: bool,

                 remember_only_action:bool, 
                 remember_only_post_think:bool):
     self.show_last_action = show_last_action
     self.header_for_new_state = header_for_new_state
     self.remember_only_action = remember_only_action
     self.remember_only_post_think = remember_only_post_think
     self.remember_only_valid = remember_only_valid
     self.api_funcs_only = api_funcs_only
     self.remember_only_correct = remember_only_correct
     if remember_only_correct:
        self.remember_only_valid = True
     
  def create_prompt(self):
    prompt = ""
    if self.initial_prompt:
      if self.initial_prompt_multiplayer:
        if self.name == self.world.agent1.name:
            prompt += INITIAL_PROMPT_MULTI_PLAYER.format(self.name, self.world.agent2.name)
        elif self.name == self.world.agent2.name:
            prompt += INITIAL_PROMPT_MULTI_PLAYER.format(self.name, self.world.agent1.name)
      else:
         prompt += INITIAL_PROMPT.format(self.name)

      #TODO: Uncomment self.initial_prompt = False
      self.initial_prompt = False
    else:  
      if self.show_last_action:
        prompt += self.last_action_res + "\n"
    if self.header_for_new_state:
      prompt += "Updated World State\n-------------------\n"


    for rev_item_name in self.revealed_items:
      rev_item = self.world.items.get(rev_item_name, None)
      if rev_item == None:
        continue
      if self.api_funcs_only:
        prompt += rev_item.print_item_func_only()
      else:
        prompt += rev_item.print_item()
      if rev_item.examined:
        for rev_rev_item in rev_item.examine_reveals:
            if rev_rev_item not in self.revealed_items:
                self.revealed_items.append(rev_rev_item)
      if rev_item.unlocked:
          for rev_rev_item in rev_item.unlock_reveals:
              if rev_rev_item not in self.revealed_items:
                  self.revealed_items.append(rev_rev_item)
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
    post_think_response = ""

    self.render_prompt(prompt)
    done_thinking = False
    self.is_thinking = True
    num_thinks = 0
    num_tokens = 0
    print("Thinking", end="", flush=True)
    for chunk in stream:
      part = chunk['message']['content']
      response = response + part
      num_tokens += 1
      if response.find("</think>") != -1:
        done_thinking = True
        self.is_thinking = False
      if done_thinking:
        print(part, end="")
        post_think_response = post_think_response + part
      else:
        print(".", end="", flush=True)
        num_thinks += 1
        self.world.engine.old_draw_agent_view(self)
        pygame.display.flip()
        # agent.world.clock.tick(60)
    print(f"num_tokens[{num_tokens}]{self.name}")
    print(f"num_thinks[{num_thinks}]{self.name}")
    python_start = response.find("```python")
    python_start += 10
    python_end = response[python_start:].find("```")
    python_instr = response[python_start:][:python_end]
    print("\n", end="")
    print(self.name + ">", end="")
    print(python_instr, end="")

    cmd = python_instr

    exe_res = execute_command(self, cmd)
    
    if exe_res.find("ERR") != -1 and self.remember_only_valid:
       return
    
    if exe_res == "Incorrect combination" and self.remember_only_correct:
        return

    if self.remember_only_action:
      self.messages.append({
      'role': 'assistant',
      'content': cmd,
      })
    elif self.remember_only_post_think:
      self.messages.append({
      'role': 'assistant',
      'content': post_think_response,
      })
    else:
      self.messages.append({
        'role': 'assistant',
        'content': response,
      })
    
    # print(self.messages)
 
    
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
    return "ERR No function"
  pre_dot = cmd[:dot_ind]
  post_dot = cmd[dot_ind:]
  cur_item = agent.world.items.get(pre_dot, None)
  # if cur_item == None or pre_dot not in agent.revealed_items:
  #   print("Item not found\n", end="")
  #   return agent.turn()
  if not isinstance(cur_item, Item): # this variation allows examine for nearby unrevealed items
    return "ERR Item not found"
  
  if cur_item.name not in agent.revealed_items:
     return "ERR Item not revealed"

  if agent.agent_type == Agent_Type.LLM and cur_item.name in agent.revealed_items:
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

    # have other agents also get examine info if in same room as agent making examine call
    if agent.world.agent1.name != agent.name and agent.get_room().name == agent.world.agent1.get_room().name:
      cur_item.examine(agent.world.agent1)
    if agent.world.agent2.name != agent.name and agent.get_room().name == agent.world.agent2.get_room().name:
      cur_item.examine(agent.world.agent2)
   
    # if agent.agent_type == Agent_Type.LLM:
    #   agent.last_action_res = result
    return result
  if pre_dot not in agent.revealed_items:
    return "ERR Item not revealed"
  if post_dot.startswith(".examine("):
    # print(cur_item.name, end="")
    print(f"[exec] calling examine on {pre_dot}")

    return cur_item.examine(agent)
  if post_dot.startswith(".unlock("):
    cur_combo = post_dot[8:post_dot.find(')')]
    print(f"[exec] trying unlock({cur_combo}) on {pre_dot}")
    if cur_item.examined == False:
       cur_item.examine(agent=agent)
    success = cur_item.unlock(cur_combo, agent=agent)
    print(cur_item.unlock_attempts)
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