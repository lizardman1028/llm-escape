from enum import Enum

class Unlock_Type(Enum):
  none = 0
  int = 1
  str = 2

class Agent_Type(Enum):
  CLI = 0
  LLM = 1
  TERMINAL_UI = 2

class Item_Type(Enum):
  ITEM = 0
  ROOM = 1