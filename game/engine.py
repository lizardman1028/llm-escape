import pygame
import pygame.freetype
from game.server import GameServer
from game.llm_game import LLMGame
from config import *
from game.rules import get_escape_room_rules
from world import Agent, Item, execute_command
# from pygame_agent import PygameAgent
from our_enums import *

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

        self.interaction_items = []
        self.interaction_texts = []
        self.api_key_bindings = {}
        self.awaiting_unlock_target = None

    def handle_event(self, event, agent : Agent):
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
                    if self.awaiting_unlock_target:
                        item_name = self.awaiting_unlock_target
                        cmd = f"{item_name}.unlock({self.human_input_text})"
                        result = execute_command(agent, cmd)
                        self.last_human_result = result if result else f"You performed `{cmd}`."
                        self.awaiting_unlock_target = None
                    else:
                        cmd = self.human_input_text
                        result = execute_command(agent, cmd)
                        self.last_human_result = result if result else f"You performed `{cmd}`."
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

            elif not self.human_input_mode:
                # print(f"KEYDOWN: event.key={event.key}, unicode={event.unicode}")
                key_char = event.unicode
                if not key_char:
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        key_char = str(event.key - pygame.K_0)

                # If we're in unlock input mode, handle input there
                if self.human_input_mode and self.awaiting_unlock_target:
                    prompt = f"Enter password for {self.awaiting_unlock_target}: {self.human_input_text}"
                    input_text = self.font.render(prompt, True, (255, 255, 255))
                    self.screen.blit(input_text, (10, SCREEN_HEIGHT - 100))
                    if event.key == pygame.K_RETURN:
                        item_name = self.awaiting_unlock_target
                        cmd = f"{item_name}.unlock({self.human_input_text})"
                        result = execute_command(agent, cmd)
                        self.last_human_result = result if result else f"You performed `{cmd}`."
                        self.human_input_text = ""
                        self.human_input_mode = False
                        self.awaiting_unlock_target = None
                        return
                    elif event.key == pygame.K_BACKSPACE:
                        self.human_input_text = self.human_input_text[:-1]
                    else:
                        self.human_input_text += event.unicode
                    return
                if key_char in self.unlock_bindings:
                    self.human_input_mode = True
                    self.awaiting_unlock_target = self.unlock_bindings[key_char]
                    self.human_input_text = ""
                    return

                if key_char in self.api_key_bindings:
                    cmd = self.api_key_bindings[key_char]
                    result = execute_command(agent, cmd)
                    self.last_human_result = result if result else f"You performed `{cmd}`."

        elif event.type == pygame.KEYUP:
            self.key_pressed.discard(event.key)

    def update(self, agent: Agent):
        self.human_action_displayed = False
        if not self.game_started or self.win_message or self.selected_player == "god":
            return

        dx = dy = 0
        if pygame.K_w in self.key_pressed: dy -= 5
        if pygame.K_s in self.key_pressed: dy += 5
        if pygame.K_a in self.key_pressed: dx -= 5
        if pygame.K_d in self.key_pressed: dx += 5

        # print(f"dx:{dx}, dy:{dy}")
        new_x = agent.x + dx
        new_y = agent.y + dy

        # Check if agent in a room, if so, clamp position to within that room (agents should hopefully always be in rooms)
        room_item = agent.get_room()
        print(f"room name: {room_item.name}")
        if room_item.name == "":
            pass
        else:
            cur_x, cur_y = agent.x, agent.y
            agent.x, agent.y = new_x, new_y
            new_room_item=agent.get_room()
            if new_room_item.name != "":
                new_x, new_y = new_room_item.pygame_object.nearest_interior_pt(new_x, new_y)
            else:
                new_x, new_y = room_item.pygame_object.nearest_interior_pt(new_x, new_y)

        
        agent.x, agent.y = new_x, new_y
        # print(f"cur_x:{agent.x} cur_y:{agent.y}")

        collision_names, collision_items = self.player_item_collisions(agent)
        # print("revealed_items =", agent.revealed_items)
        # for item in collision_items:
        #     if item.name not in agent.revealed_items:
        #         agent.revealed_items.append(item.name)
        #         print(f"Added {item.name} to revealed_items")

        self.interaction_items = collision_items
        self.api_key_bindings.clear()
        self.unlock_bindings = {} 

        if not self.human_input_mode:
            action_index = 1
            for item in collision_items:
                if not item.examined:
                    # Allow examine for nearby items even if not yet revealed
                    self.api_key_bindings[str(action_index)] = f"{item.name}.examine()"
                    action_index += 1
                # if item.examined and item.unlock_type != Unlock_Type.none and not item.unlocked:
                #     self.api_key_bindings[str(action_index)] = f"{item.name}.unlock({item.unlock_combination})"
                #     action_index += 1
                elif item.examined and item.unlock_type != Unlock_Type.none and not item.unlocked:
                    self.api_key_bindings[str(action_index)] = f"{item.name}.unlock(...)"
                    self.unlock_bindings[str(action_index)] = item.name 
                    action_index += 1

        print(f"interactable objects {collision_names}")

    # def player_item_collisions(self, agent: Agent) -> tuple[list[str], list[Item]]:
    #     collision_names = []
    #     collision_items = []
    #     for revealed_name in agent.revealed_items:
    #         revealed_item = agent.world.items.get(revealed_name, None)
    #         if revealed_item == None:
    #             continue
    #         if revealed_item.pygame_object.in_player_radius(agent.x, agent.y):
    #             collision_names.append(revealed_name)
    #             collision_items.append(revealed_item)
    #     return collision_names, collision_items

    # This version reveals API calls for nearby items, even when they haven't officially been revealed via examine yet
    def player_item_collisions(self, agent: Agent) -> tuple[list[str], list[Item]]:
        collision_names = []
        collision_items = []

        for name in agent.revealed_items:
            item = agent.world.items.get(name, None)
            if item:
                collision_names.append(name)
                collision_items.append(item)

        revealed_rooms = [
            item for name, item in agent.world.items.items()
            if name in agent.revealed_items and item.item_type == Item_Type.ROOM
        ]

        for name, item in agent.world.items.items():
            if name in agent.revealed_items:
                continue
            if item.item_type != Item_Type.ITEM:
                continue
            for room in revealed_rooms:
                if room.pygame_object.player_inside(item.pygame_object.center_x, item.pygame_object.center_y):
                    if item.pygame_object.in_player_radius(agent.x, agent.y):
                        collision_names.append(name)
                        collision_items.append(item)
                    break

        return collision_names, collision_items

    def draw_agent_view(self, agent: Agent):
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
            revealed_rooms = [
                item for name, item in agent.world.items.items()
                if name in agent.revealed_items and item.item_type == Item_Type.ROOM
            ]
            for room in revealed_rooms:
                room.pygame_object.draw(self.screen)

            for name, item in agent.world.items.items():
                if item.item_type == Item_Type.ITEM:
                    for room in revealed_rooms:
                        if room.pygame_object.player_inside(item.pygame_object.center_x, item.pygame_object.center_y):
                            item.pygame_object.draw(self.screen)

            pygame.draw.circle(self.screen, COLOR_PLAYER, (agent.x, agent.y), PLAYER_RADIUS)

            if self.interaction_items and not self.human_input_mode:
                box_x, box_y = 20, SCREEN_HEIGHT - 150
                pygame.draw.rect(self.screen, (50, 50, 50), (box_x, box_y, 300, 130))
                pygame.draw.rect(self.screen, (180, 180, 180), (box_x, box_y, 300, 130), 2)
                y_offset = 0
                for key, action in self.api_key_bindings.items():
                    # print(f"Binding [{key}] → {action}")
                    text = self.font.render(f"[{key}] {action}", True, (255, 255, 255))
                    self.screen.blit(text, (box_x + 10, box_y + 10 + y_offset))
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
