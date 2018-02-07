from pybrain.rl.environments.task import Task

from utils import *


class HASSHTask(Task):

    def __init__(self, environment):
        super(HASSHTask, self).__init__(environment)
        self.env = environment
        self.lastreward = 0

    def performAction(self, action):
        self.env.performAction(action)

    def getObservation(self):
        sensors = self.env.getSensors()
        return sensors

    def getReward(self):
        reward = getCurrentReward()
        cur_reward = self.lastreward
        self.lastreward = reward
        return cur_reward

    @property
    def indim(self):
        return self.env.indim

    @property
    def outdim(self):
        return self.env.outdim
