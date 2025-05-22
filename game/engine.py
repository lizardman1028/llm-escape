import pygame
import pygame.freetype
from game.server import GameServer
from game.llm_game import LLMGame
from config import *
from game.rules import get_escape_room_rules

def circle_rect_collision(cx, cy, radius, rect):
    closest_x = max(rect.left, min(cx, rect.right))
    closest_y = max(rect.top, min(cy, rect.bottom))
    dx = closest_x - cx
    dy = closest_y - cy
    return dx * dx + dy * dy <= radius * radius

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
        self.game_started = False

    def handle_event(self, event):
        if not self.game_started and event.type == pygame.MOUSEBUTTONDOWN:
            pos = pygame.mouse.get_pos()
            button_x, button_y = SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 20
            if button_x <= pos[0] <= button_x + 100 and button_y <= pos[1] <= button_y + 40:
                self.game_started = True
        elif not self.game_started:
            return

        if self.human_input_mode:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    cmd = self.human_input_text
                    result = self.server.process_api_call("human", cmd)
                    self.last_human_result = result if result else f"You performed `{cmd}`."
                    self.human_input_text = ""
                    self.human_input_mode = False
                    self.human_action_displayed = True
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
        self.human_action_displayed = False
        if not self.game_started or self.win_message or self.selected_player == "god":
            return

        dx = dy = 0
        if pygame.K_w in self.key_pressed: dy -= 5
        if pygame.K_s in self.key_pressed: dy += 5
        if pygame.K_a in self.key_pressed: dx -= 5
        if pygame.K_d in self.key_pressed: dx += 5

        player = self.server.state.players[self.selected_player]
        new_x = player.x + dx
        new_y = player.y + dy

        # Define room boundaries
        padding = 8
        if player.room == "main":
            min_x = padding
            max_x = SCREEN_WIDTH // 2 - padding
        else:
            min_x = SCREEN_WIDTH // 2 + padding
            max_x = SCREEN_WIDTH - padding
        min_y = padding
        max_y = SCREEN_HEIGHT - padding

        # Clamp inside room
        player.x = max(min_x, min(max_x, new_x))
        player.y = max(min_y, min(max_y, new_y))

        # Detect object collisions
        for obj in self.server.state.get_room_objects(player.room):
            obj_rect = None
            message = None

            if obj.kind == "door":
                obj_rect = pygame.Rect(obj.x - 10, obj.y - 30, 20, 60)
                message = "A locked door." if obj.locked else "An unlocked door."
            elif obj.kind == "cabinet":
                obj_rect = pygame.Rect(obj.x - 20, obj.y - 20, 40, 40)
                message = "A cabinet."
            elif obj.kind == "computer":
                obj_rect = pygame.Rect(obj.x - 20, obj.y, 40, 40)
                message = "A computer terminal."

            if obj_rect and circle_rect_collision(player.x, player.y, PLAYER_RADIUS, obj_rect):
                if not self.human_action_displayed:
                    self.last_human_result = message

                # Door logic
                if obj.kind == "door":
                    if obj.id == "to_hidden":
                        if obj.locked:
                            self.last_human_result = "The entry door is locked."
                        else:
                            player.room = "hidden"
                            player.x = SCREEN_WIDTH - 100
                            player.y = SCREEN_HEIGHT // 2
                            self.last_human_result = "You passed into the hidden room."

                    elif obj.id == "to_main":
                        if obj.locked:
                            self.last_human_result = "The door back to the main room is locked."
                        else:
                            player.room = "main"
                            player.x = 100
                            player.y = SCREEN_HEIGHT // 2
                            self.last_human_result = "You returned to the main room."

                    elif obj.id == "exit":
                        if obj.locked:
                            self.last_human_result = "The exit door is locked."
                        else:
                            self.win_message = "You escaped the room!"

    def draw(self):
        self.screen.fill(COLOR_BG)

        if not self.game_started:
            for i, line in enumerate(self.rules_text[:10]):
                rule = self.font.render(line, True, (120, 120, 120))
                self.screen.blit(rule, (10, 10 + i * 18))
            button_x, button_y = SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 20
            pygame.draw.rect(self.screen, (100, 100, 100), (button_x, button_y, 100, 40))
            start_text = self.font.render("Start", True, (255, 255, 255))
            self.screen.blit(start_text, (button_x + 20, button_y + 10))
        else:
            if self.selected_player == "god":
                drawn_rooms = set()
                for _, player in self.server.state.players.items():
                    if player.room not in drawn_rooms:
                        self._draw_room_border(player.room)
                        drawn_rooms.add(player.room)
                for name, player in self.server.state.players.items():
                    pygame.draw.circle(self.screen, COLOR_LLM if name == "llm" else COLOR_PLAYER,
                                       (int(player.x), int(player.y)), PLAYER_RADIUS)
                    for obj in self.server.state.get_room_objects(player.room):
                        self._draw_object(obj.kind, obj.x, obj.y)
            else:
                state = self.server.get_state_for_player(self.selected_player)
                self._draw_room_border(state["player"]["room"])
                player = state["player"]
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

    def _draw_object(self, kind, x, y):
        if kind == "computer":
            pygame.draw.polygon(self.screen, COLOR_COMPUTER, [(x, y), (x + 20, y + 40), (x - 20, y + 40)])
        elif kind == "cabinet":
            pygame.draw.rect(self.screen, COLOR_CABINET, (x - 20, y - 20, 40, 40))
        elif kind == "door":
            pygame.draw.rect(self.screen, COLOR_DOOR, (x - 10, y - 30, 20, 60))

    def _draw_room_border(self, room_name):
        border_color = (100, 100, 100)
        thickness = 8
        if room_name == "main":
            pygame.draw.rect(self.screen, border_color, (0, 0, SCREEN_WIDTH // 2, thickness))
            pygame.draw.rect(self.screen, border_color, (0, SCREEN_HEIGHT - thickness, SCREEN_WIDTH // 2, thickness))
            pygame.draw.rect(self.screen, border_color, (SCREEN_WIDTH // 2 - thickness, 0, thickness, SCREEN_HEIGHT))
            pygame.draw.rect(self.screen, border_color, (0, 0, thickness, SCREEN_HEIGHT // 2 - 40))
            pygame.draw.rect(self.screen, border_color, (0, SCREEN_HEIGHT // 2 + 40, thickness, SCREEN_HEIGHT // 2 - 40))
        elif room_name == "hidden":
            pygame.draw.rect(self.screen, border_color, (SCREEN_WIDTH // 2, 0, SCREEN_WIDTH // 2, thickness))
            pygame.draw.rect(self.screen, border_color, (SCREEN_WIDTH // 2, SCREEN_HEIGHT - thickness, SCREEN_WIDTH // 2, thickness))
            pygame.draw.rect(self.screen, border_color, (SCREEN_WIDTH - thickness, 0, thickness, SCREEN_HEIGHT))
            pygame.draw.rect(self.screen, border_color, (SCREEN_WIDTH // 2, 0, thickness, SCREEN_HEIGHT // 2 - 40))
            pygame.draw.rect(self.screen, border_color, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40, thickness, SCREEN_HEIGHT // 2 - 40))

    def _distance(self, player, obj):
        return ((player.x - obj.x)**2 + (player.y - obj.y)**2)**0.5
