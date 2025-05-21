import pygame
import pygame.freetype
from game.server import GameServer
from game.llm_game import LLMGame
from config import *
from game.rules import get_escape_room_rules

class GameEngine:
    def __init__(self, screen):
        self.screen = screen
        self.server = GameServer(split_start=True)
        self.llm = LLMGame()
        self.font = pygame.font.SysFont(None, 24)
        self.input_font = pygame.freetype.SysFont(None, 20)

        self.view_modes = ["human", "llm", "god"]
        self.view_index = 0
        self.selected_player = self.view_modes[self.view_index]

        self.key_pressed = set()
        self.last_llm_action = ""
        self.human_input_mode = False
        self.human_input_text = ""
        self.last_human_result = ""
        self.win_message = ""

        self.rules_text = get_escape_room_rules().splitlines()

    def handle_event(self, event):
        if self.human_input_mode:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    response = self.server.process_api_call("human", self.human_input_text)
                    self.last_human_result = f"Human: {self.human_input_text} -> {response}"
                    self.human_input_text = ""
                    self.human_input_mode = False
                elif event.key == pygame.K_BACKSPACE:
                    self.human_input_text = self.human_input_text[:-1]
                else:
                    self.human_input_text += event.unicode
            return

        if event.type == pygame.KEYDOWN:
            self.key_pressed.add(event.key)

            if event.key == pygame.K_l:
                response = self.llm.get_action(None)
                result = self.server.process_api_call("llm", response)
                self.last_llm_action = f"LLM: {response} -> {result}"

            elif event.key == pygame.K_h:
                self.human_input_mode = True
                self.human_input_text = ""

            elif event.key == pygame.K_TAB:
                self.view_index = (self.view_index + 1) % len(self.view_modes)
                self.selected_player = self.view_modes[self.view_index]

        elif event.type == pygame.KEYUP:
            self.key_pressed.discard(event.key)

    def update(self):
        if self.win_message or self.selected_player == "god":
            return

        dx = dy = 0
        if pygame.K_w in self.key_pressed:
            dy -= 5
        if pygame.K_s in self.key_pressed:
            dy += 5
        if pygame.K_a in self.key_pressed:
            dx -= 5
        if pygame.K_d in self.key_pressed:
            dx += 5

        player = self.server.state.players[self.selected_player]
        self.server.state.move_player(self.selected_player, dx, dy)

        for obj in self.server.state.get_room_objects(player.room):
            if obj.kind == "door":
                dist = ((player.x - obj.x)**2 + (player.y - obj.y)**2)**0.5
                if dist < 30:
                    if hasattr(obj, "locked") and not obj.locked:
                        if player.room == "main":
                            player.room = "hidden"
                            player.x, player.y = 100, 300
                        elif player.room == "hidden":
                            self.win_message = "You escaped the room!"
                    else:
                        self.last_human_result = "The door is locked."

    def draw(self):
        self.screen.fill(COLOR_BG)

        if self.selected_player == "god":
            for name, player in self.server.state.players.items():
                pygame.draw.circle(self.screen, COLOR_LLM if name == "llm" else COLOR_PLAYER,
                                   (int(player.x), int(player.y)), PLAYER_RADIUS)
                for obj in self.server.state.get_room_objects(player.room):
                    kind, x, y = obj.kind, obj.x, obj.y
                    self._draw_object(kind, x, y)
        else:
            state = self.server.get_state_for_player(self.selected_player)
            player = state["player"]

            pygame.draw.rect(self.screen, (50, 50, 50), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 4)
            pygame.draw.circle(self.screen, COLOR_PLAYER, (int(player["x"]), int(player["y"])), PLAYER_RADIUS)

            for obj in state["objects"]:
                self._draw_object(obj["kind"], obj["x"], obj["y"])

            y_offset = 10
            for msg in state["shared_info"][-5:]:
                text = self.font.render(msg, True, (200, 200, 200))
                self.screen.blit(text, (SCREEN_WIDTH - 300, y_offset))
                y_offset += 20

        if self.last_llm_action:
            info = self.font.render(self.last_llm_action[:80], True, (180, 180, 255))
            self.screen.blit(info, (10, SCREEN_HEIGHT - 70))

        if self.last_human_result:
            hinfo = self.font.render(self.last_human_result[:80], True, (255, 255, 180))
            self.screen.blit(hinfo, (10, SCREEN_HEIGHT - 50))

        if self.human_input_mode:
            pygame.draw.rect(self.screen, (60, 60, 60), (10, SCREEN_HEIGHT - 30, 600, 25))
            self.input_font.render_to(self.screen, (15, SCREEN_HEIGHT - 28), self.human_input_text, (255, 255, 255))

        if self.win_message:
            win_text = self.font.render(self.win_message, True, (0, 255, 0))
            self.screen.blit(win_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))

        if self.selected_player in ["god", "human"]:
            for i, line in enumerate(self.rules_text[:10]):
                rule = self.font.render(line, True, (120, 120, 120))
                self.screen.blit(rule, (10, 10 + i * 18))

    def _draw_object(self, kind, x, y):
        if kind == "computer":
            pygame.draw.polygon(self.screen, COLOR_COMPUTER, [(x, y), (x + 20, y + 40), (x - 20, y + 40)])
        elif kind == "cabinet":
            pygame.draw.rect(self.screen, COLOR_CABINET, (x - 20, y - 20, 40, 40))
        elif kind == "door":
            pygame.draw.rect(self.screen, COLOR_DOOR, (x - 15, y - 30, 30, 60))
