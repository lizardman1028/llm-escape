import sys
import pygame
from world import Agent, Item, World, Wheel, LLM_Agent, PairDoor, VALID_PAIRS
from game.engine import GameEngine
from config import SCREEN_WIDTH, SCREEN_HEIGHT
from pygame_agent import PygameAgent
from pygame_object import PygameObject
from our_enums import *

def make_wheel_item(name, labels, pos, color=(200, 100, 100)):
    pygame_obj = PygameObject(color, *pos, 40, 40)
    wheel = Wheel(                             
        name=name,
        examine_out=f"A rotating wheel with {len(labels)} options.",
        labels=labels,
        pygame_object=pygame_obj
    )
    wheel.current = None
    return wheel

def main(config_string=None):
    items = {}

    if config_string == "passage_of_time":
        print("Running 'passage_of_time' configuration!")
        zodiac_labels = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]
        number_labels = [str(i) for i in range(1, 13)]

        clues_player1 = """1. It’s not your turn, but listen. 2. The Earth first had balance, before evolution started. 3. It’s not your turn, but listen. 4. Cats will proudly say they evolved halfway through. 5. It’s not your turn, but listen. 6. Humans came dead last, and sometimes two brains are better than one. 7. It’s not your turn, but listen."""

        clues_player2 = """1. Woke up and ate breakfast, and found some salmon in the refrigerator. What a prime time to be lucky! 2. It’s not your turn, but listen. 3. Read some children’s books prior to lunch and got so hungry for pork, I could have wolfed it down. Didn’t have any, so settled for beef instead. 4. It’s not your turn, but listen. 5. Went out for dinner and tried asking my German waiter about random access memory, but she flatly said no. The nice rack of lamb I ended up sampling was good, though. 6. It’s not your turn, but listen. 7. Decided on a late-night dessert of honey-coated insects, which left a sharp aftertaste. Watched some soccer and thought about the team I could assemble, down to each player."""

        items["paper_zodiac"] = Item("paper_zodiac", clues_player1, pygame_object=PygameObject((255, 255, 255), 320, 100, 80, 30))
        items["paper_numbers"] = Item("paper_numbers", clues_player2, pygame_object=PygameObject((255, 255, 255), 580, 140, 80, 30))

        items["wheel"] = make_wheel_item(
            name="wheel", 
            labels=zodiac_labels, 
            pos=(SCREEN_WIDTH // 2 - 60, SCREEN_HEIGHT // 3),
            color=(200, 100, 100)
        )

        items["wheel2"] = make_wheel_item(
            name="wheel2", 
            labels=number_labels, 
            pos=(SCREEN_WIDTH // 2 + 20, SCREEN_HEIGHT // 3),
            color=(100, 200, 200)
        )

        items["wall_note"] = Item(
            name="wall_note",
            examine_out="Scrawled across the wall in fading ink: 'Pairs of values will connect you across space. The wheels turn... one on each side.'",
            pygame_object=PygameObject((255, 255, 180), 500, 40, 60, 20),
            examine_reveals=[]
        )

        items["door_hidden"] = PairDoor(
            name="door_hidden",
            hint_text="Seven pairs... and maybe there's a wheel in another room...",
            valid_pairs=VALID_PAIRS,
            pygame_object=PygameObject(
                (0, 120, 255),
                SCREEN_WIDTH // 2 - 10,
                SCREEN_HEIGHT * 2 // 3,
                20,
                100,
            ),
        )

        items["door_exit"] = Item(
            name="door_exit",
            examine_out="A final exit door with a keypad lock.",
            unlock_type=Unlock_Type.str,
            unlock_combination="Ophiuchus 13",
            pygame_object=PygameObject(
                (0, 255, 100),
                SCREEN_WIDTH - 30,
                100,
                20, 100
            )
        )

        items["room_main"] = Item(
            name="room_main",
            examine_out="You are in a room. Perhaps another player is out there.",
            examine_reveals=["wheel", "door_hidden", "paper_zodiac"],
            pygame_object=PygameObject(
                (255, 200, 200),
                0, 0,
                SCREEN_WIDTH // 2, SCREEN_HEIGHT
            ),
            item_type=Item_Type.ROOM
        )

        items["room_hidden"] = Item(
            name="room_hidden",
            examine_out="You are in a room. Maybe someone is on the other side.",
            examine_reveals=["wheel2", "door_exit", "paper_numbers"],
            pygame_object=PygameObject(
                (200, 200, 255),
                SCREEN_WIDTH // 2, 0,
                SCREEN_WIDTH // 2, SCREEN_HEIGHT
            ),
            item_type=Item_Type.ROOM
        )

        world = World(items=items)
        world.engine = GameEngine(world.screen)
        world.agent1 = PygameAgent("Player1", ["room_main"], world)
        world.agent2 = LLM_Agent("LLM_player", ["room_hidden"], world=world)
        world.start()
        return

    # Default fallback room setup (used when config_string is not passage_of_time)
    pygame_room = PygameObject((255, 200, 200), 0, 0, 500, 500)
    pygame_room2 = PygameObject((200, 200, 255), 500, 100, 300, 100)
    pygame_book = PygameObject((255, 0, 0), 300, 100, 10, 30)
    pygame_door = PygameObject((0, 0, 255), 490, 100, 20, 100)

    items = {
        "room": Item("room", "You are in a big room. You see a book and a door.",
                     examine_reveals=["book", "door"],
                     pygame_object=pygame_room,
                     item_type=Item_Type.ROOM),
        "book": Item("book", "There's something written inside: 1234",
                     pygame_object=pygame_book,
                     item_type=Item_Type.ITEM),
        "room2": Item("room2", "You discovered a hidden room!",
                      pygame_object=pygame_room2,
                      item_type=Item_Type.ROOM),
        "door": Item("door", "A locked door. Maybe it leads somewhere.",
                     unlock_type=Unlock_Type.int,
                     unlock_combination="1234",
                     examine_reveals=[],
                     unlock_reveals=["room2"],
                     pygame_object=pygame_door,
                     item_type=Item_Type.ITEM)
    }

    world = World(items=items)
    world.engine = GameEngine(world.screen)
    world.agent1 = PygameAgent("Player1", ["room"], world)
    world.agent2 = LLM_Agent("LLM_player", ["room"], world=world)
    world.start()

if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else None
    main(config_string=config)
