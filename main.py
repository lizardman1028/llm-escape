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
    items = {
        "room":Item("room", "", pygame_object=pygame_room, item_type=Item_Type.ROOM),
        "book":Item("book", "", pygame_object=pygame_book, item_type=Item_Type.ITEM),
        "room2":Item("room2", "", pygame_object=pygame_room2, item_type=Item_Type.ROOM)
        }
    world = World(items=items)
    agent = PygameAgent("Player", ["room", "book", "room2"], world)

    agent.turn()
    

if __name__ == "__main__":
    main()