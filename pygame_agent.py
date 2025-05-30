import pygame
import world
from world import Agent, Item, World
import sys
from game.engine import GameEngine
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from our_enums import *

class Player:
    def __init__(self, name, room, x, y):
        self.name = name
        self.room = room
        self.x = x
        self.y = y
        self.known_info = []
# Agent class

class PygameAgent(Agent):
    name : str
    agent_type : world.Agent_Type
    revealed_items : list[str] = []
    x: int
    y: int
    
    def __init__(self, name, revealed_items, world : World):
        self.name = name
        self.revealed_items = revealed_items
        self.world = world 
        self.agent_type = Agent_Type.CLI
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Escape Room: Human and LLM")

        self.clock = pygame.time.Clock()
        self.engine = GameEngine(self.screen)
        self.shouldnt_break = True

        self.x = 200
        self.y = 200

    def turn(self):
        self.engine.draw_agent_view(self)
        # for item_name in self.revealed_items:
        #     item_obj = self.world.items[item_name]
        #     item_obj.pygame_object.draw(self.screen)
        while self.shouldnt_break:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.engine.handle_event(event, self)

            self.engine.update(self)
            # self.engine.draw()
            self.engine.draw_agent_view(self)
            # for item_name in self.revealed_items:
            #     item_obj = self.world.items[item_name]
            #     item_obj.pygame_object.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)
    
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

# def main():
#     # pygame.init()
#     # screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
#     # pygame.display.set_caption("Escape Room: Human vs LLM")

#     # clock = pygame.time.Clock()
#     # engine = GameEngine(screen)

#     while True:  # turn
#         for event in pygame.event.get():
#             if event.type == pygame.QUIT:
#                 pygame.quit()
#                 sys.exit()
#             engine.handle_event(event)

#         engine.update()
#         engine.draw()
#         pygame.display.flip()
#         clock.tick(60)

# if __name__ == "__main__":
#     main()
