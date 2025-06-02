# def get_escape_room_rules():
#     return """
# Welcome to the Escape Room!

# Please observe the following rules:
# - Do not damage or force open any objects.
# - Nothing in the room requires climbing or dangerous actions.
# - If an object is locked, try to find a way to open it with logic.
# - Computers may require passwords — try looking around for clues.
# - Doors may be electronically locked. Try unlocking them by interacting with the environment.
# - File cabinets may contain puzzles or clues — not all drawers are useful.
# - Communication is key. Use the shared system to pass information.
# - Solving all puzzles will eventually lead to escape. Good luck!

# (Subtle Hint: What’s written on paper might be needed on a keypad. The computer won’t take just anything.)
# """

def get_escape_room_rules() -> str:
    return (
        "GAME RULES\n"
        "-----------\n"
        "• Use the arrow/WASD keys to move.\n"
        "• Press number keys to call the suggested API action.\n"
        "• [0] starts a text chat with the other player using share().\n"
        "• Seven zodiac–number pairs (in any order) unlock the *interior* door:\n"
        "      Pisces-7 · Libra-1 · Taurus-3 · Leo-6 · Aries-9 · Gemini-12 · Scorpio-11\n"
        "• You can also input a pair directly:  door_hidden.unlock(\"Leo 6\")\n"
        "• The final exit opens with one phrase hidden somewhere in the game.\n"
        "• LLM player must reply with **one** Python call wrapped in markdown.\n"
    )

