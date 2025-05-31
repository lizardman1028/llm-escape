import pygame
from world import Agent, Item, World
from game.engine import GameEngine
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from pygame_agent import PygameAgent
from pygame_object import PygameObject
from our_enums import *

def main():
    
    pygame_room = PygameObject((255,200,200), 0, 0, 500, 500)
    pygame_room2 = PygameObject((200,200,255), 500, 100, 300, 100)
    pygame_book = PygameObject((255,0,0), 300, 100, 10, 30)
    pygame_door = PygameObject((255, 0, 0), 400, 250, 20, 60)
    items = {
        "room":Item("room", "You are in a big room. You see a book and a door.", examine_reveals=["book", "door"], pygame_object=pygame_room, item_type=Item_Type.ROOM),
        "book":Item("book", "There's something written inside: 1234", pygame_object=pygame_book, item_type=Item_Type.ITEM),
        "room2":Item("room2", "You discovered a hidden room!", pygame_object=pygame_room2, item_type=Item_Type.ROOM),
        "door": Item("door", "A locked door. Maybe it leads somewhere.", unlock_type=Unlock_Type.int, unlock_combination="1234", examine_reveals=[], unlock_reveals=["room2"], pygame_object=pygame_door, item_type=Item_Type.ITEM)}
    world = World(items=items)
    agent = PygameAgent("Player", ["room"], world)

    agent.turn()
    

if __name__ == "__main__":
    main()