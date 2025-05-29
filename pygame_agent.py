import pygame
import world
from world import Agent, Item, World
import sys
from game.engine import GameEngine
from config import SCREEN_WIDTH, SCREEN_HEIGHT

# Agent class

class PygameAgent(Agent):
    name : str
    agent_type : world.Agent_Type
    revealed_items : list[str] = []
    def __init__(self, name, revealed_items, world : World):
        self.name = name
        self.revealed_items : list[Item] = revealed_items
        self.world = world 
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Escape Room: Human and LLM")

        self.clock = pygame.time.Clock()
        self.engine = GameEngine(self.screen)
        self.shouldnt_break = True

    def turn(self):
        for item in self.revealed_items:
            item_obj = self.world.items[item]
            item_obj.pygame_object.draw(self.screen)

        while self.shouldnt_break:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                self.engine.handle_event(event, self)

            self.engine.update()
            self.engine.draw()
            item_obj.pygame_object.draw(self.screen)
            pygame.display.flip()
            self.clock.tick(60)

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
