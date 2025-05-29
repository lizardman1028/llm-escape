import pygame
from world import Agent, Item, World
from game.engine import GameEngine
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from pygame_agent import PygameAgent
from pygame_object import PygameObject

def main():
    
    pygame_object = PygameObject([255,255,255], 10, 10)
    items = {"rectangle":Item("rectangle", "", pygame_object=pygame_object)}
    world = World(items=items)
    agent = PygameAgent("Player", ["rectangle"], world)

    agent.turn()
    

if __name__ == "__main__":
    main()