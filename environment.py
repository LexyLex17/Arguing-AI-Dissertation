import random

import utils


class Environment:

    ## Creating environment

    def __init__(self, map_path):
        self.file_path = map_path
        self.world = self.load_assets(self.load_map())

    def load_map(self):
        try:
            with open(self.file_path) as f:
                world_map = row = [[col.lower() for col in line.strip()] for line in f]

                # quick error check
                first_row = len(world_map[0])
                for row in world_map:
                    if len(row) != first_row:
                        raise Exception("Map rows are not even")
                return world_map
        except FileNotFoundError:
            print(f"File not found")
        except PermissionError:
            print(f"File read permissions were denied")
        except IOError as e:
            print(f"IO error: {e}")

        return []

    def load_assets(self, world_map:list):
        for i in range(len(world_map)):
            for j in range(len(world_map[i])):
                if world_map[i][j] == 'u' or world_map[i][j] == 'd' or world_map[i][j] == 'l' or world_map[i][j] == 'r':
                    world_map[i][j] = utils.ChargingStation((i, j), world_map[i][j])
                elif world_map[i][j] == '^' or world_map[i][j] == 'v' or world_map[i][j] == '<' or world_map[i][j] == '>':
                    world_map[i][j] = utils.Roomba((i, j), world_map[i][j])
        return world_map

    def get_cells(self, positions:list) -> dict[tuple[int,int],...]:
        cells = {}
        for pos in positions:
            cells[pos] = self.world[pos[0]][pos[1]]
        return cells

    def __str__(self):
        out = ""
        for row in self.world:
            for col in row:
                out += f"{col}\t"
            out += "\n"
        return out

    ## End of environment creation

    ## Function that allows the roomba to see if the space in front of it is available to move into
    def move_to(self, position, to, environment):
        x = position[1] + to[1]
        y = position[0] + to[0]
        '''if environment.world[y][x] == ' ':
            print("Valid move")
            return True''' # No longer needed due to blanks being replaced with weights
        if environment.world[y][x] == 'x':
            print("Invalid move (Barrier)")
            return False
        elif environment.world[y][x] == 'u':
            print("Invalid move (Charging Station)")
            return False
        else:
            return True


if __name__ == "__main__":
    e = Environment("floorplan.txt")

    for i in range(len(e.world)):
        for j in range(len(e.world[i])):
            if e.world[i][j] == " ":
                e.world[i][j] = random.randint(0,100)

    ## Setting robots
    roomba = e.world[10][3]
    charging_Station = e.world[11][3]

    ## Stating initial "conditions"
    print("Starting conditions:")
    print(f"\nRoomba: \n\t{roomba.__str__()}, Position: {roomba.position}\n\tCurrent Tile: {roomba.currentCleaning}")
    print(f"Charging Station: \n\t{charging_Station.__str__()}, Position: {charging_Station.position}\n")
    print(e)

    ## Start of MAIN cycles
    for i in range(200):
        print("=" * 70)
        if roomba.stateOfCharge < 100:
            if charging_Station.act(e):
                roomba.stateOfCharge += 5
                if roomba.stateOfCharge > 100:
                    roomba.stateOfCharge = 100
                print("Roomba charged!")
                print(f"Roomba SoC: {roomba.stateOfCharge}%")
                roomba.previousOutput = "Roomba charged!"

            else:
                if roomba.act(e):
                    print("Roomba out of charge!")
                    break  # Ends cycles if roomba has no charge
        else:
            if roomba.act(e):
                print("Roomba out of charge!")
                break  # Ends cycles if roomba has no charge
        print(roomba.printRoombaMap())
