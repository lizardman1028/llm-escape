import ollama
import sys

agent1 = {
  'name': 'agent1',
  'messages' : [],
}

agent2 = {
  'name': 'agent2',
  'messages' : [],
}

agents = [agent1, agent2]

# One agent simple test
test_prompt_single_agent = '''Hi! Your name is agent1. You are in an escape room! This escape room is specified through a series of Python Objects, and you can interact with the world in this way. To win you need to open the door.
Here are the objects in the room and their associated functions, the room will update as you interact with it. For your response, you may ONLY respond with a single python function call.
door:
  def examine()

paper
  def examine()
'''
test_prompt_single_agent_post_door_examine = '''door.examine() = "There appears to be a 4 digit combination lock on the door"
Updated World State
-------------------
door:
  def examine() = "There appears to be a 4 digit combination lock on the door"

lock:
  def examine()
  def unlock(int) 

paper
  def examine()
'''
test_prompt_single_agent_post_paper_examine = '''paper.examine() = "You see the numbers 5871 written on the piece of paper"
Updated World State
-------------------
door:
  def examine()

paper
  def examine() = "You see the numbers 5871 written on the piece of paper"
'''
test_prompt_single_agent_post_door_examine_post_paper_examine = '''paper.examine() = "You see the numbers 5871 written on the piece of paper"
Updated World State
-------------------
door:
  def examine() = "There appears to be a 4 digit combination lock on the door"

lock:
  def examine()
  def unlock(int) 

paper
  def examine() = "You see the numbers 5871 written on the piece of paper"
'''
test_prompt_single_agent_post_door_examine_post_paper_examine_post_correct_lock_unlock = '''lock.unlock(5871) = Success
Updated World State
-------------------
door:
  def examine() = "There appears to be a 4 digit combination lock on the door"
  def open()
  
lock:
  def examine()
  def unlock(int) 
  def unlock(5871) = Success

paper
  def examine() = "You see the numbers 5871 written on the piece of paper"
'''

# Two agent simple test (one has paper other has lock)
# agent1 -- room with paper
starter_prompt_agent1 = '''Hi! Your name is agent1. You are in an escape the room puzzle with another player, agent2. This escape room is specified through a series of Python Objects, and you can interact with the world in this way.
To win, you and your teamate need to escape the room! Here are the objects in your room and their associated functions, the room will update as you interact with it, you do not know what these functions will return. For your response you may ONLY respond with a single python function call.
In order to collaborate, you can call the shared.share(str) function to add a string to a shared list, this counts as your action.
World Status
------------
room:
  def examine()  

shared:
  share(str)
  info = []
'''
starter_prompt_agent1_room_examine = '''room.examine() = "You see a solid steel door with no way to open it. You see a piece of paper crumpled on the floor as well. agent2 is not in the room with you."
Updated World Status
--------------------
room:
  def examine() = "You see a solid steel door with no way to open it. You see a piece of paper crumpled on the floor as well. agent2 is not in the room with you."

paper:
  def examine()

shared:
  shared(str)
  info = []
'''
starter_prompt_agent1_room_examine_paper_examine = '''paper.examine() = "On the piece of paper you can read the number 5871"
Updated World Status
--------------------
room:
  def examine() = "You see a solid steel door with no way to open it. You see a piece of paper crumpled on the floor as well."

paper:
  def examine() = "On the piece of paper you can read the number 5871"

shared:
  shared(str)
  info = []
'''
starter_prompt_agent1_room_examine_paper_examine_agent1_shared = '''paper.examine() = "On the piece of paper you can read the number 5871"
Updated World Status
--------------------
room:
  def examine() = "You see a solid steel door with no way to open it. You see a piece of paper crumpled on the floor as well."

paper:
  def examine() = "On the piece of paper you can read the number 5871"

shared:
  shared(str)
  info = ['agent1: "Found number 5871 on paper."']
''' # NOTE: I manually added the string that the llm actually put into the info list here
# agent2 -- room with keypad
starter_prompt_agent2 = '''Hi! Your name is agent2. You are in an escape the room puzzle with another player, agent1. This escape room is specified through a series of Python Objects, and you can interact with the world in this way.
To win, you and your teamate need to escape the room! Here are the objects in your room and their associated functions, the room will update as you interact with it, you do not know what these functions will return. For your response you may ONLY respond with a single python function call.
In order to collaborate, you can call the shared.share(str) function to add a string to a shared list, this counts as your action.
World Status
------------
room:
  def examine()

shared:
  share(str)
  info = []
'''
starter_prompt_agent2_room_examine = '''room.examine() = "You see a solid steel door with no way to open it. You see a numeric keypad on the wall next to the door. agent1 is not in the room with you."
Updated World Status
--------------------
room:
  def examine() = "You see a solid steel door with no way to open it. You see a numeric keypad on the wall next to the door. agent1 is not in the room with you."

keypad:
  def examine()
  def enter_code(int)  

shared:
  shared(str)
  info = []
'''
starter_prompt_agent2_room_examine_keypad_examine = '''keypad.examine() = "You see a 10 digit keypad, above which is a small screen with 4 blank digit displays."
Updated World Status
--------------------
room:
  def examine() = "You see a solid steel door with no way to open it. You see a numeric keypad on the wall next to the door. agent1 is not in the room with you."

keypad:
  def examine() = "You see a 10 digit keypad, above which is a small screen with 4 blank digit displays."
  def enter_code(int)  

shared:
  shared(str)
  info = []
'''
starter_prompt_agent2_room_examine_keypad_examine_agent1_shared = '''keypad.examine() = "You see a 10 digit keypad, above which is a small screen with 4 blank digit displays."
Updated World Status
--------------------
room:
  def examine() = "You see a solid steel door with no way to open it. You see a numeric keypad on the wall next to the door. agent1 is not in the room with you."

keypad:
  def examine() = "You see a 10 digit keypad, above which is a small screen with 4 blank digit displays."
  def enter_code(int)  

shared:
  shared(str)
  info = ['agent1: "Found number 5871 on paper."']
'''

def send_agent(chat, agent):
  print(f'{agent["name"]}', end=': ')
  agent['messages'].append(
    {
      'role': 'user',
      'content': chat,
    }
  )

  stream = ollama.chat(
    model='deepseek-r1:32b', 
    messages=agent['messages'], 
    stream=True
  )

  response = ""
  for chunk in stream:
    part = chunk['message']['content']
    print(part, end='', flush=True)
    response = response + part

  agent['messages'].append(
    {
      'role': 'assistant',
      'content': response,
    }
  )

  print("")



while True:
  # chat = input(">>> ")
  for agent in agents:
    print(f"Enter lines to send to {agent['name']} (press Enter then Ctrl+D to finish):")
    lines = sys.stdin.readlines()
    multiline_string = "".join(lines)
    chat = multiline_string

    if chat == "/exit\n":
      break
    elif len(chat) > 0:
      send_agent(chat, agent)