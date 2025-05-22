from enum import Enum
import curses
from curses import wrapper
import time
import ollama

class Unlock_Type(Enum):
  none = 0
  int = 1
  str = 2

class Agent_Type(Enum):
  CLI = 0
  LLM = 1
  TERMINAL_UI = 2

INITIAL_PROMPT = "Hi! Your name is {}. You are in an escape room! This escape room is specified through a series of Python Objects, and you can interact with the world in this way. To win you need to open the door.\
Here are the objects in the room and their associated functions, the room will update as you interact with it. For your response, you may ONLY respond with a single python function call present in the API.\n Your response is ONE line of python annotated with markdown ```python obj.examine() ```. You may not try multiple functions.\n"

shared = []

revealed_items = []

class Agent:
  name : str
  agent_type : Agent_Type
  revealed_items : list[str] = []
  def __init__(self, name, revealed_items):
    self.name = name
    self.revealed_items = revealed_items

  def turn(self, stdscr : curses.window):
    raise NotImplementedError("Interface does not implement turn function")

class CLI_Agent(Agent):
  def __init__(self, name, revealed_items):
    self.name = name
    self.revealed_items = revealed_items
    self.agent_type = Agent_Type.CLI
  
  def turn(self, stdscr : curses.window):
    stdscr.clear()
    stdscr.refresh()
    self.render_world(stdscr)
    curses.nocbreak()
    curses.echo()
    stdscr.addstr(f"{self.name}>")
    user_action_bytes = stdscr.getstr()
    user_action = user_action_bytes.decode('utf-8')
    stdscr.refresh()
    curses.cbreak()
    curses.noecho()
    dot_ind = user_action.find('.')
    open_ind = user_action.find('(')
    close_ind = user_action.find('(')
    if dot_ind == -1 or open_ind == -1 or close_ind == -1:
      stdscr.addstr("Function not found\n")
      return self.turn(stdscr)
    pre_dot = user_action[:dot_ind]
    post_dot = user_action[dot_ind:]
    cur_item = items.get(pre_dot, None)
    if cur_item == None or pre_dot not in self.revealed_items:
      stdscr.addstr("Item not found\n")
      stdscr.refresh()
      return self.turn(stdscr)
    if post_dot == ".examine()":
      cur_item.examine(self)
      stdscr.refresh()
    if post_dot.find(".unlock(") == 0:
      cur_combo = post_dot[8:-1]
      cur_item.unlock(cur_combo)
      stdscr.refresh()

  def render_world(self, stdscr : curses.window):
    for rev_item_name in self.revealed_items:
      rev_item = items.get(rev_item_name, None)
      if rev_item == None:
        continue
      # print(rev_item.print_item())
      stdscr.addstr(rev_item.print_item())
      stdscr.refresh()

class LLM_Agent(Agent):
  messages = []
  model : str
  initial_prompt : bool = True
  last_action_res : str
  
  def __init__(self, name, revealed_items, model='deepseek-r1:32b'):
    self.name = name
    self.revealed_items = revealed_items
    self.model = model
    self.agent_type = Agent_Type.LLM

  def create_prompt(self):
    prompt = ""
    if self.initial_prompt:
      prompt += INITIAL_PROMPT.format(self.name)
      self.initial_prompt = False
    else:
      prompt += self.last_action_res
    for rev_item_name in self.revealed_items:
      rev_item = items.get(rev_item_name, None)
      if rev_item == None:
        continue
      prompt += rev_item.print_item()
    return prompt
  
  def render_prompt(self, stdscr : curses.window, prompt):
    stdscr.addstr(prompt)
    stdscr.refresh()
  
  def turn(self, stdscr):
    prompt = self.create_prompt()
    self.messages.append({
      'role': 'user',
      'content': prompt,
    })
    stream = ollama.chat(
      model='deepseek-r1:32b', 
      messages=self.messages, 
      stream=True
    )

    stdscr.refresh()

    response = ""
    
    self.render_prompt(stdscr, prompt)
    done_thinking = False
    stdscr.addstr("Thinking")
    for chunk in stream:
      part = chunk['message']['content']
      response = response + part
      if response.find("</think>") != -1:
        done_thinking = True
      if done_thinking:
        stdscr.addstr(part)
      else:
        stdscr.addstr(".")
      stdscr.refresh()
    
    self.messages.append({
      'role': 'assistant',
      'content': response,
    })

    python_start = response.find("```python")
    python_start += 10
    python_end = response[python_start:].find("```")
    python_instr = response[python_start:][:python_end]
    stdscr.addstr("\n")
    stdscr.addstr(self.name + ">")
    stdscr.addstr(python_instr)
    stdscr.refresh()

    cmd = python_instr
    
    dot_ind = cmd.find('.')
    open_ind = cmd.find('(')
    close_ind = cmd.find('(')
    if dot_ind == -1 or open_ind == -1 or close_ind == -1:
      stdscr.addstr("Function not found\n")
      return self.turn(stdscr)
    pre_dot = cmd[:dot_ind]
    post_dot = cmd[dot_ind:]
    cur_item = items.get(pre_dot, None)
    if cur_item == None or pre_dot not in self.revealed_items:
      stdscr.addstr("Item not found\n")
      return self.turn(stdscr)
    if post_dot.find(".examine(") == 0:
      stdscr.addstr(cur_item.name)
      self.last_action_res = cur_item.examine(self)
      return self.last_action_res
      stdscr.refresh()
    if post_dot.find(".unlock(") == 0:
      cur_combo = post_dot[8:-1]
      cur_item.unlock(cur_combo)

    # result = execute_command(self, python_instr, stdscr)
    # self.last_action_res = str(result)
    # stdscr.refresh()
    # TODO: finish LLM Turn, then start GUI interface


def print_world(stdscr : curses.window):
  for rev_item_name in revealed_items:
    rev_item = items.get(rev_item_name, None)
    if rev_item == None:
      continue
    # print(rev_item.print_item())
    stdscr.addstr(rev_item.print_item())
    stdscr.refresh()

def print_agent_world(stdscr : curses.window, agent: Agent):
  for rev_item_name in agent.revealed_items:
    rev_item = items.get(rev_item_name, None)
    if rev_item == None:
      continue
    # print(rev_item.print_item())
    stdscr.addstr(rev_item.print_item())
    stdscr.refresh()

class Item:
  name : str = ""
  examine_out : str = ""
  examined : bool = False
  examine_reveals : list[str] 
  unlock_type : Unlock_Type = Unlock_Type.none
  unlock_combination : str = ""
  unlock_attempts : list = []
  unlocked : bool = False
  def __init__(self, name : str, examine_out : str, unlock_type : Unlock_Type = Unlock_Type.none, unlock_combination : str ="", examine_reveals : list[str] = []):
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
  def examine(self, agent : Agent):
    self.examined = True
    for item_name in self.examine_reveals:
      agent.revealed_items.append(item_name)
    if agent.agent_type == Agent_Type.LLM:
      return f"{self.name}.examine() = {self.examine_out}"
    return self.examine_out
  def unlock(self, combination):
    if combination == self.unlock_combination:
      self.unlocked = True
    else:
      self.unlock_attempts.append(combination)
    return combination == self.unlock_combination

def share(agent : Agent, msg):
  shared.append(f"{agent.name}: {msg}")

def execute_command(agent, cmd, stdscr : curses.window):
  dot_ind = cmd.find('.')
  open_ind = cmd.find('(')
  close_ind = cmd.find('(')
  if dot_ind == -1 or open_ind == -1 or close_ind == -1:
    stdscr.addstr("Function not found\n")
    return agent.turn(stdscr)
  pre_dot = cmd[:dot_ind]
  post_dot = cmd[dot_ind:]
  cur_item = items.get(pre_dot, None)
  if cur_item == None or pre_dot not in agent.revealed_items:
    stdscr.addstr("Item not found\n")
    return agent.turn(stdscr)
  if post_dot == ".examine()":
    stdscr.addstr(cur_item.name)
    return cur_item.examine(agent)
    stdscr.refresh()
  if post_dot.find(".unlock(") == 0:
    cur_combo = post_dot[8:-1]
    cur_item.unlock(cur_combo)

items = {
  "room":Item("room", "you see a room", examine_reveals=["door", "paper"]), 
  "door":Item("door", "the door has a combination lock on it", examine_reveals=["lock"]),
  "paper":Item("paper", "The paper has the number 5871 written on it"),
  "lock":Item("lock", "the lock has a numeric keyboard with 4 spots for digits", unlock_type=Unlock_Type.int, unlock_combination="5871")}
revealed_items = ["room"]

cli_agent =  CLI_Agent("Cli Agent", ["room"])
llm_agent = LLM_Agent("LLM_Agent", ["room"])

def main(stdscr : curses.window):
  while True:
    # cli_agent.turn(stdscr)
    llm_agent.turn(stdscr)
    # cli_agent.turn(stdscr)
    # print_agent_world(stdscr, llm_agent)
    # stdscr.addstr(str(llm_agent.revealed_items))
    stdscr.refresh()
    stdscr.clear()
    time.sleep(1)
  
wrapper(main)