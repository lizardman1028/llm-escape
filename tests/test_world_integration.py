from game.server import GameServer
from game.world_model import print_world, revealed_items

def test_reveal_and_unlock():
    print("--- Initial World State ---")
    print(print_world())

    server = GameServer()

    print("\n--- Step 1: Examine paper ---")
    print(server.process_api_call("human", "paper.examine()"))
    print(print_world())

    print("\n--- Step 2: Examine door ---")
    print(server.process_api_call("human", "door.examine()"))
    print(print_world())

    print("\n--- Step 3: Unlock lock with correct code ---")
    print(server.process_api_call("human", "lock.unlock(5871)"))
    print(print_world())

    print("\n--- Step 4: Try unlocking door (GUI object logic) ---")
    print(server.process_api_call("human", "door.unlock()"))
    print(print_world())

if __name__ == "__main__":
    test_reveal_and_unlock()
