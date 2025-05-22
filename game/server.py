from game.state import GameState
from config import SCREEN_WIDTH

class GameServer:
    def __init__(self, split_start=False):
        self.state = GameState(split_start=split_start)
        self.api_log = []

    def process_api_call(self, player_name, api_call):
        self.api_log.append((player_name, api_call))
        result = f"{player_name} called {api_call}"

        player = self.state.players[player_name]
        profile = self.state.profiles[player_name]
        room_objects = self.state.get_room_objects(player.room)

        try:
            if api_call == "paper.examine()":
                result = "You see the number 1234."
                player.known_info.append("paper: 1234")

            elif api_call.startswith("shared.share("):
                message = api_call.split("(")[1][1:-2]
                self.state.shared_info.append(f"{player_name}: {message}")
                result = "Message shared."

            elif api_call.startswith("cabinet.open_drawer("):
                drawer_index = int(api_call.split("(")[1].rstrip(")"))
                for obj in room_objects:
                    if obj.kind == "cabinet":
                        result = obj.open_drawer(drawer_index)
                        break

            elif api_call.startswith("cabinet.unlock_drawer("):
                drawer_index = int(api_call.split("(")[1].rstrip(")"))
                for obj in room_objects:
                    if obj.kind == "cabinet":
                        result = obj.unlock_drawer(drawer_index)
                        break

            elif api_call.startswith("computer.submit("):
                text = api_call.split("(")[1][1:-2]
                for obj in room_objects:
                    if obj.kind == "computer":
                        result = obj.submit(text, room_objects)
                        break

            elif api_call == "door.examine()":
                for obj in room_objects:
                    if obj.kind == "door":
                        result = "The door is locked." if obj.locked else "The door is unlocked."
                        break
                else:
                    result = "No door found."

            elif api_call == "door.unlock()":
                for obj in room_objects:
                    if obj.kind == "door":
                        if obj.locked:
                            obj.locked = False
                            result = "You unlocked the door."
                        else:
                            result = "The door is already unlocked."
                        break
                else:
                    result = "No door found."

            elif api_call.startswith("lock.unlock("):
                guess = api_call.split("(")[1].rstrip(")")
                # Hardcoded check for now
                if guess == "5871":
                    # Find the exit door in hidden room (left wall)
                    for obj in self.state.get_room_objects("hidden"):
                        if obj.kind == "door" and obj.x < SCREEN_WIDTH // 2:
                            obj.locked = False
                            result = "You hear a click. The exit door is now unlocked."
                            break
                    else:
                        result = "Could not find the exit door."
                else:
                    result = "Incorrect code."

            elif api_call.startswith("puzzle.attempt("):
                guess = api_call.split("(")[1][1:-2]
                for obj in room_objects:
                    if obj.kind == "puzzle":
                        result = obj.attempt(guess)
                        if obj.is_solved():
                            profile.add_clue(f"{obj.id} solved")
                        break

            else:
                result = f"No valid API matched for `{api_call}`."

        except Exception as e:
            result = f"Error processing call: {e}"

        return result

    def get_state_for_player(self, player_name):
        player = self.state.players[player_name]
        room_objects = self.state.get_room_objects(player.room)
        return {
            "player": vars(player),
            "objects": [obj.to_dict() for obj in room_objects],
            "shared_info": self.state.shared_info
        }
