import pygame
from world import Agent, Item, World
from game.engine import GameEngine
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from pygame_agent import PygameAgent
from pygame_object import PygameObject
from our_enums import *

def main():
    
    pygame_object = PygameObject((255,255,255), 0, 0, 500, 500)
    items = {
        "rectangle":Item("rectangle", "", pygame_object=pygame_object, item_type=Item_Type.ROOM)
        # "book":Item("rectangle", "", pygame_object=pygame_object, item_type=Item_Type.ROOM)
        }
    world = World(items=items)
    agent = PygameAgent("Player", ["rectangle"], world)

    agent.turn()
    

if __name__ == "__main__":
    main()