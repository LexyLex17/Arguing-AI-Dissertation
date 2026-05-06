from agent import Agent
import utils

class ChargingStation(Agent):

    def __init__(self, position, facing):
        super().__init__(position)
        self.facing = facing

    def decide(self, percept: dict[tuple[int,int],...], environment):
        if self.facing == 'u':
            if utils.is_Roomba(environment.world[self.position[0]-1][self.position[1]]):
                return True
        if self.facing == 'd':
            if utils.is_Roomba([1, 0]):
                return True
        if self.facing == 'l':
            if utils.is_Roomba([0, -1]):
                return True
        if self.facing == 'r':
            if utils.is_Roomba([0, 1]):
                return True
        return False

    def act(self, environment):
        decision = self.decide(self.sense(environment), environment)
        if decision:
            print("Roomba detected")
            return decision

    def __str__(self):
        return self.facing
