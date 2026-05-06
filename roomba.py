from agent import Agent
import utils
import random
import heapq
from environment import *

class Roomba(Agent):

    def __init__(self, position: tuple[int, int], facing):
        super().__init__(position)
        self.previousOutput = "Roomba Initialised"
        self.stateOfCharge = 100
        self.chargingLocation = None
        self.facing = facing
        self.currentCleaning = [None, 0]
        self.previousCleaning = [None, 0]
        self.world = self.createMap()

    def createMap(self):
        try:
            with open("roombaFogOfWar.txt") as f:
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

    def updateMap(self, percept: dict[tuple[int, int],...]):
        world = self.world
        curPos = self.position
        world[curPos[0]][curPos[1]] = self.facing
        for k, v in percept.items():
            world[k[0]][k[1]] = v

    def printRoombaMap(self):
        out = ""
        for row in self.world:
            for col in row:
                out += f"{col}\t"
            out += "\n"
        return out

    def decide(self, percept: dict[tuple[int, int],...], environment):

        print(f"Previous cycle: {self.previousOutput}")
        print(f"Current tile: {self.currentCleaning}")
        for k, v in percept.items():
            if utils.is_Charging(v):
                self.chargingLocation = k


        # Check for battery vs distance to charging station
        chargingFacing = utils.is_Charging(environment.world[self.chargingLocation[0]][self.chargingLocation[1]])
        chargingLocationAim = None
        if chargingFacing == "u":
            chargingLocationAim = (self.chargingLocation[0]-1, self.chargingLocation[1])
        elif chargingFacing == "d":
            chargingLocationAim = (self.chargingLocation[0]+1, self.chargingLocation[1])
        elif chargingFacing == "l":
            chargingLocationAim = (self.chargingLocation[0], self.chargingLocation[1]-1)
        elif chargingFacing == "r":
            chargingLocationAim = (self.chargingLocation[0], self.chargingLocation[1]+1)
        # print(chargingLocationAim)

        path = self.calc_path(self.position, chargingLocationAim, "x", environment)
        print(f"Path = {path}")
        # path + no. of turns
        totalPathMoves = 0
        if len(path) > 1:
            # Checking if the roomba is NOT facing the direction of the "path" movement
            if (self.facing != "^" or self.facing != "v") and path[1][1] != self.position[1]:
                totalPathMoves += 1
            if (self.facing != "<" or self.facing != ">") and path[1][0] != self.position[0]:
                totalPathMoves += 1
        for i in range(len(path) - 1):  # The "-1" accounts for the first item in the path - being the current location of the roomba
            totalPathMoves += 1
        for i in range(len(path) - 2):
            if path[i][0] != path[i+2][0] and path[i][1] != path[i+2][1]: # Checking to see if the x and y values are different from 2 coords (one before the turn and the one after, DOES NOT include the coord AT WHICH the turn occurs), if they are it signifies a turn
                totalPathMoves += 1


        print(totalPathMoves, self.stateOfCharge)

        if self.stateOfCharge <= totalPathMoves:
            self.currentCleaning = [None, 0]
            if len(path) > 0:
                directionY = path[1][0] - self.position[0]
                directionX = path[1][1] - self.position[1]
                direction = (directionY, directionX)
                print(direction)

                if self.facing != "^" and direction == (-1, 0):
                    return "turn up"
                elif self.facing != "v" and direction == (1, 0):
                    return "turn down"
                elif self.facing != ">" and direction == (0, 1):
                    return "turn right"
                elif self.facing != "<" and direction == (0, -1):
                    return "turn left"
                else:
                    return "move"
        else:
            # Check if there is a previously saved tile to clean
            if self.currentCleaning[0] is None:
                # Check for dirtiness of each tile + comparison
                listCompare = []
                a = (None, 0)
                b = (None, 0)
                for k, v in percept.items():
                    if isinstance(v, int):
                        listCompare.append([k, v])
                for i in listCompare:
                    if i[1] > a[1]:
                        a = i  # "Absorb" current direction's immediate dirt value (A[1])
                    elif i[1] == a[1]:
                        b = i # Fallback option if all surrounding options are 0
                if a[0] is None:
                    a = b
                self.currentCleaning = a
                # print(a)

                # Check direction toward the dirtiest tile
                directionY = a[0][0] - self.position[0]
                directionX = a[0][1] - self.position[1]
                direction = (directionY, directionX)
                # print(direction)

                if self.facing != "^" and direction == (-1, 0):
                    return "turn up"
                elif self.facing != "v" and direction == (1, 0):
                    return "turn down"
                elif self.facing != ">" and direction == (0, 1):
                    return "turn right"
                elif self.facing != "<" and direction == (0, -1):
                    return "turn left"
                else:
                    return "move"
            else:
                if self.position == self.currentCleaning[0]:
                    if self.currentCleaning[1] == 0:
                        self.previousCleaning = self.currentCleaning
                        self.currentCleaning = [None, 0]
                        return "restart"
                    else:
                        return "clean"
                else:
                    return "move"


    def act(self, environment):
        if self.stateOfCharge == 0 and self.position != (10, 3):
            return True # Ends cycles
        decision = self.decide(self.sense(environment), environment)
        if decision == "turn up":
            self.facing = "^"
            print("Roomba looked up")
            self.previousOutput = "Roomba looked up"
            self.stateOfCharge -= 1
            print(f"SOC: {self.stateOfCharge}%\n")
        elif decision == "turn down":
            self.facing = "v"
            print("Roomba looked down")
            self.previousOutput = "Roomba looked down"
            self.stateOfCharge -= 1
            print(f"SOC: {self.stateOfCharge}%\n")
        elif decision == "turn left":
            self.facing = "<"
            print("Roomba looked left")
            self.previousOutput = "Roomba looked left"
            self.stateOfCharge -= 1
            print(f"SOC: {self.stateOfCharge}%\n")
        elif decision == "turn right":
            self.facing = ">"
            print("Roomba looked right")
            self.previousOutput = "Roomba looked right"
            self.stateOfCharge -= 1
            print(f"SOC: {self.stateOfCharge}%\n")
        elif decision == "move":
            print("Roomba moved")
            self.previousOutput = "Roomba moved"
            directions = {
                0: (0, 1),  # Right
                1: (0, -1),  # Left
                2: (-1, 0),  # Up
                3: (1, 0)  # Down
            }
            if self.facing == '>':
                direction = directions[0]
            elif self.facing == '<':
                direction = directions[1]
            elif self.facing == '^':
                direction = directions[2]
            elif self.facing == 'v':
                direction = directions[3]

            #print(direction)
            curPos = self.position
            newPos = self.move(environment, direction)
            envWor = environment.world
            #print(newPos)
            newPosBool = newPos[0]
            newPosVal = newPos[1]
            envWor[ newPosVal[0] ][ newPosVal[1] ] = self.previousCleaning[1]
            if newPosBool:
                #print(f"Current: ({curPos}, {envWor[ curPos[0] ][ curPos[1] ]}) -> ({newPosVal}, {envWor[ newPosVal[0] ][ newPosVal[1] ]})")

                (envWor[ curPos[0] ][ curPos[1] ], envWor[ newPosVal[0] ][ newPosVal[1] ]) \
                                                =\
                (envWor[ newPosVal[0] ][ newPosVal[1] ], envWor[ curPos[0] ][ curPos[1] ])
                self.stateOfCharge -= 1
                print(f"SOC: {self.stateOfCharge}%\n")
        elif decision == "clean":
            self.previousOutput = "Roomba cleaned tile"
            self.currentCleaning[1] -= 10
            if self.currentCleaning[1] < 0:
                self.currentCleaning[1] = 0
            print(f"Current tile weight: {self.currentCleaning[1]}")
            self.stateOfCharge -= 1
            print(f"SOC: {self.stateOfCharge}%\n")
        elif decision == "restart":
            print("restarted cycle")
            self.act(environment) # Restart the decision process WITHOUT removing a charge % as the robot HAS NOT DECIDED to do anything at this point - see flow diagram in report
        self.updateMap(self.sense(environment))

    def move(self, environment, to):
        if environment.move_to(self.position, to, environment):
            xNew = self.position[1] + to[1]
            #print(f"xNew : {xNew}")
            yNew = self.position[0] + to[0]
            #print(f"yNew : {yNew}")
            self.position = (yNew, xNew)
            output = [True, self.position]
            return output
        else:
            return [False, None]

    def __str__(self):
        return self.facing

    # MANHATTAN DISTANCE FUNCTIONS

    def calc_path(self, start, goal, avoid, e):
        p_queue = []
        heapq.heappush(p_queue, (0, start))

        directions = {
            "right": (0, 1),
            "left": (0, -1),
            "up": (-1, 0),
            "down": (1, 0)
        }
        predecessors = {start: None}
        g_values = {start: 0}

        while len(p_queue) != 0:
            current_cell = heapq.heappop(p_queue)[1]
            if current_cell == goal:
                return self.get_path(predecessors, start, goal)
            for direction in ["up", "right", "down", "left"]:
                row_offset, col_offset = directions[direction]
                neighbour = (current_cell[0] + row_offset, current_cell[1] + col_offset)

                if self.viable_move(neighbour[1], neighbour[0], avoid, e) and neighbour not in g_values:
                    cost = g_values[current_cell] + 1
                    g_values[neighbour] = cost
                    f_value = cost + self.calc_distance(goal, neighbour)
                    heapq.heappush(p_queue, (f_value, neighbour))
                    predecessors[neighbour] = current_cell

    def get_path(self, predecessors, start, goal):
        current = goal
        path = []
        while current != start:
            path.append(current)
            current = predecessors[current]
        path.append(start)
        path.reverse()
        return path

    def viable_move(self, x, y, types, environment):
        if environment.world[y][x] != 'x':
            return True
        else:
            return False

    def calc_distance(self, point1: tuple[int, int], point2: tuple[int, int]):
        x1, y1 = point1
        x2, y2 = point2
        return abs(x1 - x2) + abs(y1 - y2)

    # END OF MANHATTAN DISTANCE FUNCTIONS

