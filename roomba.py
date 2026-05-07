from agent import Agent
import utils
import random
import heapq
from environment import *
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

class Roomba(Agent):

    def __init__(self, position: tuple[int, int], facing):
        super().__init__(position)
        self.startingPosition = position
        self.returning = False
        self.previousOutput = "Roomba Initialised"
        self.stateOfCharge = 100
        self.chargingLocation = None
        self.facing = facing
        self.currentCleaning = [None, 0]
        self.previousCleaning = [self.position, 0]
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
        print(f"Current tile: {self.currentCleaning[0]}\n\tWeight: {self.currentCleaning[1]}")
        print(f"Previous tile: {self.previousCleaning[0]}, {self.previousCleaning[1]}")

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

        if self.position == chargingLocationAim:
            self.currentCleaning = [None, 0]
            self.previousCleaning = [None, 0]   # Erases the current cleaning once the roomba has reached the original location (Pathfound back to the station)
            self.returning = False

        path = self.calc_path(self.position, chargingLocationAim, "x", environment)
        # print(f"Path = {path}")
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


        print(f"Path length: {totalPathMoves}")

        if self.stateOfCharge <= (totalPathMoves + 5):
            self.previousCleaning = self.currentCleaning
            self.returning = True
            print(self.previousCleaning[1])

            if len(path) > 0:
                directionY = path[1][0] - self.position[0]
                directionX = path[1][1] - self.position[1]
                direction = (directionY, directionX)

                if self.facing != "^" and direction == (-1, 0):
                    return "turn up"
                elif self.facing != "v" and direction == (1, 0):
                    return "turn down"
                elif self.facing != ">" and direction == (0, 1):
                    return "turn right"
                elif self.facing != "<" and direction == (0, -1):
                    return "turn left"
                else:
                    self.currentCleaning = [(self.position[0] + direction[0], self.position[1] + direction[1]),
                                            environment.world[self.position[0] + direction[0]][
                                                self.position[1] + direction[1]]]
                    print(self.currentCleaning)
                    return "move"
        else:
            # Check if there is a previously saved tile to clean
            self.returning = False
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
            #print(self.previousCleaning[1])
            if newPosBool:
                #print(f"Current: ({curPos}, {envWor[ curPos[0] ][ curPos[1] ]}) -> ({newPosVal}, {envWor[ newPosVal[0] ][ newPosVal[1] ]})")

                (envWor[ curPos[0] ][ curPos[1] ], envWor[ newPosVal[0] ][ newPosVal[1] ]) \
                                                =\
                (envWor[ newPosVal[0] ][ newPosVal[1] ], envWor[ curPos[0] ][ curPos[1] ])
                envWor[ curPos[0] ][ curPos[1] ] = self.previousCleaning[1]
                # print(envWor[ curPos[0] ][ curPos[1] ])
                self.stateOfCharge -= 1
                print(f"SOC: {self.stateOfCharge}%\n")
        elif decision == "clean":
            self.previousOutput = "Roomba cleaned tile"
            self.clean(self.currentCleaning[1], self.stateOfCharge)
            print(f"Current tile weight: {self.currentCleaning[1]}")
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

    def clean(self, tileWeight, batterySOC):

        print(tileWeight, batterySOC)

        batteryLevel = ctrl.Antecedent(np.arange(0, 100, 10), 'batteryLevel')
        dirtiness = ctrl.Antecedent(np.arange(0, 100, 10), 'dirtiness')
        fanSpeedC = ctrl.Consequent(np.arange(0, 100, 10), 'fanSpeedCon')
        fanSpeedA = ctrl.Antecedent(np.arange(0, 100, 10), 'fanSpeedAnt')
        batteryDrainage = ctrl.Consequent(np.arange(0, 10, 1), 'batteryDrainage')
        cleaningRate = ctrl.Consequent(np.arange(1, 20, 1), 'cleaningRate')

        # Battery level
        batteryLevel['low'] = fuzz.zmf(batteryLevel.universe, 10, 33)
        batteryLevel['medium'] = fuzz.trapmf(batteryLevel.universe, [30, 40, 50, 75])
        batteryLevel['high'] = (fuzz.smf(batteryLevel.universe, 65, 90))

        # Dirtiness
        dirtiness['low'] = fuzz.zmf(dirtiness.universe, 10, 33)
        dirtiness['medium'] = fuzz.trapmf(dirtiness.universe, [15, 40, 55, 70])
        dirtiness['high'] = (fuzz.smf(dirtiness.universe, 65, 80))

        # Fan speed A
        fanSpeedA['low'] = fuzz.zmf(fanSpeedA.universe, 10, 33)
        fanSpeedA['medium'] = fuzz.trapmf(fanSpeedA.universe, [15, 40, 55, 70])
        fanSpeedA['high'] = (fuzz.smf(fanSpeedA.universe, 60, 75))
        # Fan speed C
        fanSpeedC['low'] = fuzz.zmf(fanSpeedC.universe, 10, 33)
        fanSpeedC['medium'] = fuzz.trapmf(fanSpeedC.universe, [15, 40, 55, 70])
        fanSpeedC['high'] = (fuzz.smf(fanSpeedC.universe, 60, 75))

        # Battery Drainage
        batteryDrainage['low'] = fuzz.zmf(batteryDrainage.universe, 0, 3)
        batteryDrainage['medium'] = fuzz.trapmf(batteryDrainage.universe, [3, 4, 6, 7])
        batteryDrainage['high'] = fuzz.smf(batteryDrainage.universe, 7, 8)

        # Cleaning Rate
        cleaningRate['low'] = fuzz.zmf(cleaningRate.universe, 0, 6)
        cleaningRate['medium'] = fuzz.trapmf(cleaningRate.universe, [5, 9, 13, 15])
        cleaningRate['high'] = fuzz.smf(cleaningRate.universe, 15, 16)

        # Conditions
        sim1Condition1 = ctrl.Rule(dirtiness['low'] | batteryLevel['low'], fanSpeedC['low'])
        sim1Condition2 = ctrl.Rule(dirtiness['medium'], fanSpeedC['medium'])
        sim1Condition3 = ctrl.Rule(dirtiness['high'] & batteryLevel['high'], fanSpeedC['high'])

        sim2Condition1 = ctrl.Rule(fanSpeedA['low'], batteryDrainage['low'])
        sim2Condition2 = ctrl.Rule(fanSpeedA['medium'], batteryDrainage['medium'])
        sim2Condition3 = ctrl.Rule(fanSpeedA['high'], batteryDrainage['high'])

        sim3Condition1 = ctrl.Rule(fanSpeedA['low'], cleaningRate['low'])
        sim3Condition2 = ctrl.Rule(fanSpeedA['medium'], cleaningRate['medium'])
        sim3Condition3 = ctrl.Rule(fanSpeedA['high'], cleaningRate['high'])

        # Simulations
        fanInput = self.runSim1(tileWeight, batterySOC, [sim1Condition1, sim1Condition2, sim1Condition3])
        batteryDrainageOut = int(np.round(self.runSim2(fanInput, [sim2Condition1, sim2Condition2, sim2Condition3])))
        cleaningRateOut = int(np.round(self.runSim3(fanInput, [sim3Condition1, sim3Condition2, sim3Condition3])))

        print(f"Battery Drainage: {batteryDrainageOut}")
        print(f"Cleaning Rate: {cleaningRateOut}")
        self.stateOfCharge -= batteryDrainageOut
        self.currentCleaning[1] -= cleaningRateOut
        if self.currentCleaning[1] < 0:
            self.currentCleaning[1] = 0

    def runSim1(self, input1, input2, conditions):
        fanSpeedSim_ctrl = ctrl.ControlSystem(conditions)
        fanSpeedSim_sim = ctrl.ControlSystemSimulation(fanSpeedSim_ctrl)
        fanSpeedSim_sim.input['dirtiness'] = input1
        fanSpeedSim_sim.input['batteryLevel'] = input2
        fanSpeedSim_sim.compute()
        return fanSpeedSim_sim.output['fanSpeedCon']

    def runSim2(self, input, conditions):
        batteryDrainSim_ctrl = ctrl.ControlSystem(conditions)
        batteryDrainSim_sim = ctrl.ControlSystemSimulation(batteryDrainSim_ctrl)
        batteryDrainSim_sim.input['fanSpeedAnt'] = input
        batteryDrainSim_sim.compute()
        return batteryDrainSim_sim.output['batteryDrainage']

    def runSim3(self, input, conditions):
        cleaningSim_ctrl = ctrl.ControlSystem(conditions)
        cleaningSim_sim = ctrl.ControlSystemSimulation(cleaningSim_ctrl)
        cleaningSim_sim.input['fanSpeedAnt'] = input
        cleaningSim_sim.compute()
        return cleaningSim_sim.output['cleaningRate']

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

