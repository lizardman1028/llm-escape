import pygame
import sys
from game.engine import GameEngine
from config import SCREEN_WIDTH, SCREEN_HEIGHT

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Escape Room: Human vs LLM")

    clock = pygame.time.Clock()
    engine = GameEngine(screen)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            engine.handle_event(event)

        engine.update()
        engine.draw()
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()
