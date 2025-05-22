from game.objects.door import Door
from game.objects.computer import Computer
from game.objects.file_cabinet import FileCabinet
from game.objects.player import PlayerProfile
from config import SCREEN_WIDTH, SCREEN_HEIGHT

class GameState:
    def __init__(self, split_start=False):
        self.rooms = {
            "main": Room("Main Room"),
            "hidden": Room("Hidden Room")
        }

        # ✅ Both players start in MAIN room by default
        self.players = {
            "human": Player("human", room="main", x=100, y=300),
            "llm": Player("llm", room="main", x=300, y=300)
        }

        self.shared_info = []
        self.profiles = {name: PlayerProfile(name) for name in self.players}
        self.setup_rooms()

    def setup_rooms(self):
        # Main room: door to hidden room (left wall)
        self.rooms["main"].add_object(Door(x=20, y=SCREEN_HEIGHT // 2, locked=True, id="to_hidden"))

        self.rooms["main"].add_object(Computer(x=100, y=150, password="1234", unlock_target_id="to_hidden"))
        self.rooms["main"].add_object(
            FileCabinet(x=300, y=150,
                drawer_contents={
                    1: "Empty",
                    2: "Paper with clue: 'code = 1234'",
                    3: "Locked drawer"
                },
                locked_drawers={3: True}
            )
        )

        # Hidden room: door back to main (right wall) and exit door (left wall)
        self.rooms["hidden"].add_object(Door(x=SCREEN_WIDTH - 20, y=SCREEN_HEIGHT // 2, locked=False, id="to_main"))
        self.rooms["hidden"].add_object(Door(x=SCREEN_WIDTH // 2 + 20, y=SCREEN_HEIGHT // 2, locked=True, id="exit"))

        self.rooms["hidden"].add_object(Computer(x=500, y=150, password="exit", unlock_target_id="exit"))
        self.rooms["hidden"].add_object(
            FileCabinet(x=700, y=150,
                drawer_contents={
                    1: "Paper says: 'Final password = exit'",
                    2: "Empty",
                    3: "Locked drawer with escape plan"
                },
                locked_drawers={3: True}
            )
        )

    def get_room_objects(self, room_name):
        return self.rooms[room_name].objects

    def move_player(self, player_name, dx, dy):
        player = self.players[player_name]
        player.x += dx
        player.y += dy

class Room:
    def __init__(self, name):
        self.name = name
        self.objects = []

    def add_object(self, obj):
        self.objects.append(obj)

class Player:
    def __init__(self, name, room, x, y):
        self.name = name
        self.room = room
        self.x = x
        self.y = y
        self.known_info = []
