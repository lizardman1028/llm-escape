import pygame
from world import Agent, Item, World, LLM_Agent
from game.engine import GameEngine
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from pygame_agent import PygameAgent
from pygame_object import PygameObject
from our_enums import *

def main():
    
    pygame_room = PygameObject((255,200,200), 0, 0, 500, 500)
    pygame_room2 = PygameObject((200,200,255), 500, 100, 300, 100)
    pygame_book = PygameObject((255,0,0), 300, 100, 10, 30)
    pygame_door = PygameObject((0, 0, 255), 490, 100, 20, 100)
    pygame_paper1 = PygameObject((255,255,255), 700, 150, 10, 30)
    pygame_paper2 = PygameObject((255,255,255), 600, 150, 10, 30)
    pygame_door2 = PygameObject((0,255,0), 700, 190, 100, 20)
    pygame_room3 = PygameObject((200,255,200), 700, 200, 200, 300)
    
    old_items = {
        "room":Item("room", "You are in a big room. You see a book and a door.", examine_reveals=["book", "door"], pygame_object=pygame_room, item_type=Item_Type.ROOM),
        "book":Item("book", "There's something written inside: 1234", pygame_object=pygame_book, item_type=Item_Type.ITEM),
        "room2":Item("room2", "You discovered a hidden room!", pygame_object=pygame_room2, item_type=Item_Type.ROOM),
        "door": Item("door", "A locked door. Maybe it leads somewhere.", unlock_type=Unlock_Type.int, unlock_combination="1234", examine_reveals=[], unlock_reveals=["room2"], pygame_object=pygame_door, item_type=Item_Type.ITEM)}
    
    items = {
        "room":Item("room", "You are in a big room. You see a book and a door.", examine_reveals=["book", "door"], pygame_object=pygame_room, item_type=Item_Type.ROOM),
        "book":Item("book", "There's something written inside: 1234", pygame_object=pygame_book),
        "door": Item("door", "A locked door. Maybe it leads somewhere.", unlock_type=Unlock_Type.int, unlock_combination="1234", examine_reveals=[], unlock_reveals=["room2"], pygame_object=pygame_door, item_type=Item_Type.ITEM),
        "room2":Item("room2", "You two pieces of paper on the ground along with another locked door, the papers are indexed arbitrarily", pygame_object=pygame_room2, item_type=Item_Type.ROOM, examine_reveals=["paper1", "paper2", "door2"]),
        "paper1":Item("paper1", "The paper is ripped on its left side, on it are the numbers 52", pygame_object=pygame_paper1),
        "paper2":Item("paper2", "The paper is ripped on its right side, on it are the numbers 14", pygame_object=pygame_paper2),
        "door2":Item("door2", "A locked door with a 4 digit lock", unlock_type=Unlock_Type.int, unlock_combination="1452", unlock_reveals=["room3"], pygame_object=pygame_door2),
        "room3":Item("room3", "You Escaped the Rooms! Congrats!", pygame_object=pygame_room3, item_type=Item_Type.ROOM)}
    world = World(items=items)
    world.engine = GameEngine(world.screen)
    # agent_pygame = PygameAgent("Player1", ["room"], world)
    
    agent_llm = LLM_Agent("LLM_player", ["room"], world=world)
    agent_llm2 = LLM_Agent("LLM_player2", ["room"], world=world)
    # TTTFTTF
    
    # Prompt Formatting
    # *api funcs only*
    # Show last action
    # header for new state

    # memory
    # remember only valid
    # remember only correct 
    # only action
    # only post-think

    agent_llm.llm_config(api_funcs_only=False,
                         show_last_action=True, 
                         header_for_new_state=True, 

                         remember_only_valid=True,
                         remember_only_correct=False,
                         
                         remember_only_action=False, 
                         remember_only_post_think=True, 
                         )
    agent_llm2.llm_config(api_funcs_only=False,
                         show_last_action=True, 
                         header_for_new_state=True, 

                         remember_only_valid=True,
                         remember_only_correct=True,
                         
                         remember_only_action=False, 
                         remember_only_post_think=True, 
                         )

    world.engine.game_started = True
    # agent_pygame2 = PygameAgent("Player2", ["room"], world)
    # world.agent1 = agent_pygame
    world.agent1 = agent_llm
    # world.agent2 = agent_pygame2
    world.agent2 = agent_llm2
    
    world.start()

    # agent_llm.turn()
    

if __name__ == "__main__":
    main()