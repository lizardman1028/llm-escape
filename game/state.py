from game.objects.door import Door
from game.objects.computer import Computer
from game.objects.file_cabinet import FileCabinet
from game.objects.player import PlayerProfile

class GameState:
    def __init__(self, split_start=False):
        self.rooms = {
            "main": Room("Main Room"),
            "hidden": Room("Hidden Room")
        }
        if split_start:
            self.players = {
                "human": Player("human", room="hidden", x=100, y=300),
                "llm": Player("llm", room="main", x=300, y=300)
            }
        else:
            self.players = {
                "human": Player("human", room="main", x=100, y=300),
                "llm": Player("llm", room="main", x=300, y=300)
            }
        self.shared_info = []
        self.profiles = {name: PlayerProfile(name) for name in self.players}
        self.setup_rooms()

    def setup_rooms(self):
        self.rooms["main"].add_object(Door(x=200, y=100))
        self.rooms["main"].add_object(Computer(x=100, y=150))
        self.rooms["main"].add_object(FileCabinet(x=300, y=150))

        self.rooms["hidden"].add_object(Door(x=600, y=100, locked=True))
        self.rooms["hidden"].add_object(Computer(x=500, y=150, password="finalpass"))
        self.rooms["hidden"].add_object(FileCabinet(x=700, y=150))

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
