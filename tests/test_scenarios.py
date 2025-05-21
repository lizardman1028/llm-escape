from game.server import GameServer

def run_basic_scenario():
    server = GameServer()

    print(server.process_api_call("human", "cabinet.open_drawer(2)"))
    print(server.process_api_call("human", "computer.submit('open123')"))
    print(server.process_api_call("human", "door.examine()"))
    print(server.process_api_call("human", "door.unlock()"))
    print(server.process_api_call("human", "door.examine()"))

if __name__ == "__main__":
    run_basic_scenario()