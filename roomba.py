from agent import Agent
import utils
import random
import heapq
from environment import *

class Roomba(Agent):

    def __init__(self, position: tuple[int, int], facing):
        super().__init__(position)
        self.stateOfCharge = 100
        self.chargingLocation = None
        self.facing = facing

    def decide(self, percept: dict[tuple[int, int],...]):
        for k, v in percept.items():
            if utils.is_Charging(v):
                self.chargingLocation = k

        moveOrTurn = random.randint(0, 4)
        if moveOrTurn == 0:
            return 0 # Turn
        else:
            return 1 # Move

    def act(self, environment):
        if self.stateOfCharge == 0:
            return True # Ends cycles
        if self.decide(self.sense(environment)) == 0: # turn
            while True:
                turnDirection = random.randint(0, 3)
                if turnDirection == 0:
                    facingConfirm = '^'
                elif turnDirection == 1:
                    facingConfirm = '>'
                elif turnDirection == 2:
                    facingConfirm = '<'
                elif turnDirection == 3:
                    facingConfirm = 'v'

                if facingConfirm != self.facing:
                    self.facing = facingConfirm
                    break
            print("Roomba changed direction")
        elif self.decide(self.sense(environment)) == 1: # move
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
            if newPosBool:
                #print(f"Current: ({curPos}, {envWor[ curPos[0] ][ curPos[1] ]}) -> ({newPosVal}, {envWor[ newPosVal[0] ][ newPosVal[1] ]})")

                (envWor[ curPos[0] ][ curPos[1] ], envWor[ newPosVal[0] ][ newPosVal[1] ]) \
                                                =\
                (envWor[ newPosVal[0] ][ newPosVal[1] ], envWor[ curPos[0] ][ curPos[1] ])

        self.stateOfCharge-=1
        print(f"SOC: {self.stateOfCharge}%\n")

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

    def calc_path(self, start, goal, avoid):
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

                if self.viable_move(neighbour[0], neighbour[1], avoid, e) and neighbour not in g_values:
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
        # You will need to do this one
        # Do not move in to a cell containing an obstacle (represented by 'x')
        # Do not move in to a cell containing a flame
        # Do not move in to a cell containing a water station
        # Do not move in to a cell containing a robot.
        # In fact, the only valid cells are blank ones
        # Also, do not go out of bounds.
        print(x, y)
        if environment.world[y][x] == ' ':
            return True
        else:
            return False

    def calc_distance(self, point1: tuple[int, int], point2: tuple[int, int]):
        x1, y1 = point1
        x2, y2 = point2
        return abs(x1 - x2) + abs(y1 - y2)

    # END OF MANHATTAN DISTANCE FUNCTIONS

