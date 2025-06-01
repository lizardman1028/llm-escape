import pygame
import pygame.freetype
from game.server import GameServer
from game.llm_game import LLMGame
from config import *
from game.rules import get_escape_room_rules
from world import Agent, Item, Wheel, execute_command, share, shared, VALID_PAIRS
# from pygame_agent import PygameAgent
from our_enums import *

valid_pairs = [
    ("Pisces", "7"),
    ("Libra", "1"),
    ("Taurus", "3"),
    ("Leo", "6"),
    ("Aries", "9"),
    ("Gemini", "12"),
    ("Scorpio", "11")
]
pair_progress = set()
final_paper_spawned = False

def check_puzzle_progress(self, world):
    wheel1 = world.items.get("wheel")
    wheel2 = world.items.get("wheel2")
    if not wheel1 or not wheel2:
        return

    pair = (wheel1.current, wheel2.current)

    if pair in valid_pairs and pair not in pair_progress:
        pair_progress.add(pair)
        shared.append(f"✅ Pair {pair[0]} and {pair[1]} accepted! {len(pair_progress)}/7 correct.")

        if len(pair_progress) == 7:
            # Unlock door to room2
            connecting_door = world.items.get("door")
            if connecting_door:
                connecting_door.unlocked = True
                for agent in [world.agent1, world.agent2]:
                    if "room2" not in agent.revealed_items:
                        agent.revealed_items.append("room2")
                shared.append("🔓 The door between rooms clicks open!")

    # Final paper logic
    if len(pair_progress) == 7 and not final_paper_spawned:
        for agent in [world.agent1, world.agent2]:
            if agent.get_room().name == "room2":
                if "final_paper" not in world.items:
                    world.items["final_paper"] = Item(
                        "final_paper",
                        "A torn paper dropped from a chute. It reads: Ophiuchus 13",
                        pygame_object=PygameObject((255, 255, 0), 620, 130, 40, 20),
                        examine_reveals=[],
                    )
                for a in [world.agent1, world.agent2]:
                    if "final_paper" not in a.revealed_items:
                        a.revealed_items.append("final_paper")
                shared.append("📄 A yellow paper flutters down from a chute into the hidden room.")
                final_paper_spawned = True

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
        self.awaiting_input = None

        # self.thinking_num()

    def draw_wrapped_text(self, surface, text, font, color, x, y, max_width):
        words = text.split(' ')
        lines = []
        current_line = ""

        for word in words:
            test_line = current_line + word + " "
            if font.size(test_line)[0] < max_width:
                current_line = test_line
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())

        for i, line in enumerate(lines):
            rendered = font.render(line, True, color)
            surface.blit(rendered, (x, y + i * font.get_height()))

    def handle_event(self, event, agent: Agent):
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
                    if self.awaiting_input == "share":
                        result = share(agent, self.human_input_text)
                        self.last_human_result = result
                        self.awaiting_input = None
                        self.human_input_text = ""
                        self.human_input_mode = False
                        agent.shouldnt_break = False
                        return
                    elif self.awaiting_unlock_target:
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
                    return
                elif event.key == pygame.K_BACKSPACE:
                    self.human_input_text = self.human_input_text[:-1]
                else:
                    self.human_input_text += event.unicode
            return

        if event.type == pygame.KEYDOWN:
            self.key_pressed.add(event.key)

            if not self.human_input_mode and event.key == pygame.K_RETURN:
                agent.shouldnt_break = final_paper_spawned

            elif event.key == pygame.K_l:
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
                key_char = event.unicode
                if not key_char:
                    if pygame.K_1 <= event.key <= pygame.K_9:
                        key_char = str(event.key - pygame.K_0)

                if key_char == "0":
                    self.human_input_mode = True
                    self.human_input_text = ""
                    self.awaiting_input = "share"
                    self.last_human_result = "Enter message to share:"
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
        is_pygame_agent = agent.agent_type == Agent_Type.PYGAME_AGENT
        is_llm_agent = agent.agent_type == Agent_Type.LLM
    
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
        # print(f"room name: {room_item.name}")

        door_obj  = agent.world.items.get("door_hidden")

        # ⭐ ALLOW THROUGH DOOR when it’s unlocked
        through_door = False
        if door_obj and door_obj.unlocked:
            door_rect = door_obj.pygame_object.rect
            # Are we inside the vertical span of the doorway *and*
            # horizontally crossing the wall’s x-coordinate?
            if (door_rect.top  <= new_y <= door_rect.bottom and
                door_rect.left - PLAYER_RADIUS <= new_x <= door_rect.right + PLAYER_RADIUS):
                through_door = True

        # ---------- position clamping ----------
        if room_item.name and not through_door:
            # keep the player inside their current room
            new_x, new_y = room_item.pygame_object.nearest_interior_pt(new_x, new_y)
        # ---------------------------------------

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

        crossed_room = agent.get_room()
        if crossed_room.name and crossed_room.name not in agent.revealed_items:
            agent.revealed_items.append(crossed_room.name)

        collision_names, collision_items = self.old_player_item_collisions(agent)
        # print("revealed_items =", agent.revealed_items)
        # for item in collision_items:
        #     if item.name not in agent.revealed_items:
        #         agent.revealed_items.append(item.name)
        #         print(f"Added {item.name} to revealed_items")
        # self.interaction_items
        self.interaction_items = collision_items
        self.api_key_bindings.clear()
        self.unlock_bindings = {} 

        self.api_key_bindings["0"] = "share()"

        if not self.human_input_mode:
            action_index = 1
            for item in collision_items:
                out_txt = item.examine_out() if callable(item.examine_out) else item.examine_out
                if item.examined:
                    self.api_key_bindings[str(action_index)] = f'{item.name}.examine() = "{out_txt}"'
                    action_index += 1
                if not item.examined:
                    # Allow examine for nearby items even if not yet revealed
                    self.api_key_bindings[str(action_index)] = f"{item.name}.examine()"
                    action_index += 1
                # if item.examined and item.unlock_type != Unlock_Type.none and not item.unlocked:
                #     self.api_key_bindings[str(action_index)] = f"{item.name}.unlock({item.unlock_combination})"
                #     action_index += 1
                if item.examined and item.unlock_type != Unlock_Type.none and not item.unlocked:
                    self.api_key_bindings[str(action_index)] = f"{item.name}.unlock({item.unlock_type.name})"
                    self.unlock_bindings[str(action_index)] = item.name 
                    action_index += 1
                # if item.examined and item.unlock_type != Unlock_Type.none and item.unlocked:

                #     execute_command(agent, f"{item.name}.unlock({item.unlock_combination})")

        # print(f"interactable objects {collision_names}")

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

    def old_player_item_collisions(self, agent: Agent) -> tuple[list[str], list[Item]]:
        collision_names = []
        collision_items = []
        for revealed_name in agent.revealed_items:
            revealed_item = agent.world.items.get(revealed_name, None)
            if revealed_item == None:
                continue
            if revealed_item.pygame_object.in_player_radius(agent.x, agent.y):
                collision_names.append(revealed_name)
                collision_items.append(revealed_item)
        return collision_names, collision_items
    
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

    def old_draw_agent_view(self, agent: Agent):
     if not self.game_started:
            for i, line in enumerate(self.rules_text[:10]):
                rule = self.font.render(line, True, (120, 120, 120))
                self.screen.blit(rule, (10, 10 + i * 18))
            button_x, button_y = SCREEN_WIDTH // 2 - 50, SCREEN_HEIGHT // 2 - 20
            pygame.draw.rect(self.screen, (100, 100, 100), (button_x, button_y, 100, 40))
            start_text = self.font.render("Start", True, (255, 255, 255))
            self.screen.blit(start_text, (button_x + 20, button_y + 10))
     else:
        self.screen.fill(COLOR_BG)
        for revealed_name in agent.revealed_items:
            revealed_item = agent.world.items.get(revealed_name, None)
            if revealed_item is None:
                continue

            # ✅ Only draw if item is in the same room as the agent
            room = agent.get_room()
            if room and not room.pygame_object.player_inside(revealed_item.pygame_object.center_x, revealed_item.pygame_object.center_y):
                continue

            revealed_item.pygame_object.draw(self.screen)

            # Display wheel label if it's a Wheel and nearby
            if isinstance(revealed_item, Wheel):
                label = revealed_item.current if revealed_item.current else "(unset)"
                wheel_text = self.font.render(f"{revealed_item.name}: {label}", True, (255, 255, 255))
                tx = revealed_item.pygame_object.center_x
                ty = revealed_item.pygame_object.center_y - 25
                self.screen.blit(wheel_text, (tx - wheel_text.get_width() // 2, ty))
        # Agent1 Draw
        if agent.world.agent1.agent_type == Agent_Type.PYGAME_AGENT:
            pygame.draw.circle(self.screen, COLOR_PLAYER, (agent.world.agent1.x, agent.world.agent1.y), PLAYER_RADIUS)
            pygame.draw.circle(self.screen, (0,0,0), (agent.world.agent1.x - 7, agent.world.agent1.y - 5), 2)
            pygame.draw.circle(self.screen, (0,0,0), (agent.world.agent1.x + 7, agent.world.agent1.y - 5), 2)
            pygame.draw.rect(self.screen, (0,0,0), pygame.Rect(agent.world.agent1.x - 5, agent.world.agent1.y + 5, 10, 1))
        if agent.world.agent1.agent_type == Agent_Type.LLM:
            pygame.draw.circle(self.screen, COLOR_LLM, (agent.world.agent1.x, agent.world.agent1.y), PLAYER_RADIUS)
            pygame.draw.circle(self.screen, (0,0,0), (agent.world.agent1.x - 7, agent.world.agent1.y - 5), 2)
            pygame.draw.circle(self.screen, (0,0,0), (agent.world.agent1.x + 7, agent.world.agent1.y - 5), 2)
            pygame.draw.rect(self.screen, (0,0,0), pygame.Rect(agent.world.agent1.x - 5, agent.world.agent1.y + 5, 10, 1))
            if agent.world.agent1.is_thinking:
                thinking = self.font.render("Thinking...", True, (0,0,0))
                self.screen.blit(thinking, (agent.world.agent1.x - 20, agent.world.agent1.y - (15+18)))
        if agent.world.agent2.agent_type == Agent_Type.PYGAME_AGENT:
            pygame.draw.circle(self.screen, COLOR_PLAYER, (agent.world.agent2.x, agent.world.agent2.y), PLAYER_RADIUS)
            pygame.draw.circle(self.screen, (0,0,0), (agent.world.agent2.x - 7, agent.world.agent2.y - 5), 2)
            pygame.draw.circle(self.screen, (0,0,0), (agent.world.agent2.x + 7, agent.world.agent2.y - 5), 2)
            pygame.draw.rect(self.screen, (0,0,0), pygame.Rect(agent.world.agent2.x - 5, agent.world.agent2.y + 5, 10, 1))
        if agent.world.agent2.agent_type == Agent_Type.LLM:
            pygame.draw.circle(self.screen, COLOR_LLM, (agent.world.agent2.x, agent.world.agent2.y), PLAYER_RADIUS)
            pygame.draw.circle(self.screen, (0,0,0), (agent.world.agent2.x - 7, agent.world.agent2.y - 5), 2)
            pygame.draw.circle(self.screen, (0,0,0), (agent.world.agent2.x + 7, agent.world.agent2.y - 5), 2)
            pygame.draw.rect(self.screen, (0,0,0), pygame.Rect(agent.world.agent2.x - 5, agent.world.agent2.y + 5, 10, 1))
            if agent.world.agent2.is_thinking:
                thinking = self.font.render("Thinking...", True, (0,0,0))
                self.screen.blit(thinking, (agent.world.agent2.x - 20, agent.world.agent2.y - (15+18)))
        # pygame.draw.circle(self.screen, COLOR_PLAYER, (agent.x, agent.y), PLAYER_RADIUS)

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
        if isinstance(self.last_human_result, str) and self.last_human_result:
            self.draw_wrapped_text(
                self.screen,
                self.last_human_result,
                self.font,
                (255, 255, 180),
                10,
                10,
                max_width=580
            )
        if self.human_input_mode:
            pygame.draw.rect(self.screen, (60, 60, 60), (10, SCREEN_HEIGHT - 30, 600, 25))
            self.input_font.render_to(self.screen, (15, SCREEN_HEIGHT - 28), self.human_input_text, (255, 255, 255))
        if self.win_message:
            win_text = self.font.render(self.win_message, True, (0, 255, 0))
            self.screen.blit(win_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
        return


    def draw_agent_view(self, agent: Agent):
        self.screen.fill(COLOR_BG)

        current_room = agent.get_room()
        current_room_name = current_room.name

        if current_room_name == "room":
            pygame.draw.rect(self.screen, (0, 0, 0), (SCREEN_WIDTH//2, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT))
            current_half = pygame.Rect(0, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT)
        elif current_room_name == "room2":
            pygame.draw.rect(self.screen, (0, 0, 0), (0, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT))
            current_half = pygame.Rect(SCREEN_WIDTH//2, 0, SCREEN_WIDTH//2, SCREEN_HEIGHT)
        else:
            current_half = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)

        for name in agent.revealed_items:
            item = agent.world.items.get(name)
            if item and item.pygame_object and current_room.pygame_object.player_inside(item.pygame_object.center_x, item.pygame_object.center_y):
                item.pygame_object.draw(self.screen)

        if shared:
            popup_x = 10
            popup_y = 10
            pygame.draw.rect(self.screen, (40, 40, 40), (popup_x, popup_y, 600, 100))
            y_offset = popup_y + 8
            for msg in shared[-3:]:
                self.draw_wrapped_text(
                    self.screen,
                    msg,
                    self.font,
                    (255, 255, 255),
                    popup_x + 6,
                    y_offset,
                    max_width=588,
                )
                y_offset += 32

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
            if isinstance(self.last_human_result, str) and self.last_human_result:
                hinfo = self.font.render(self.last_human_result[:80], True, (255, 255, 180))
                self.screen.blit(hinfo, (10, SCREEN_HEIGHT - 50))
            if self.human_input_mode:
                pygame.draw.rect(self.screen, (60, 60, 60), (10, SCREEN_HEIGHT - 30, 600, 25))
                self.input_font.render_to(self.screen, (15, SCREEN_HEIGHT - 28), self.human_input_text, (255, 255, 255))
            if self.win_message:
                win_text = self.font.render(self.win_message, True, (0, 255, 0))
                self.screen.blit(win_text, (SCREEN_WIDTH // 2 - 100, SCREEN_HEIGHT // 2))
