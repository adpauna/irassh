"""
Manually control the agent to provide expert trajectories.
The main aim is to get the feature expectaitons respective to the expert trajectories manually given by the user
Use the arrow keys to move the agent around
Left arrow key: turn Left
right arrow key: turn right
up arrow key: dont turn, move forward
down arrow key: exit

Also, always exit using down arrow key rather than Ctrl+C or your terminal will be tken over by curses
"""

import numpy as np
from nn import neural_net
import pickle

NUM_STATES = 8
GAMMA = 0.9  # the discount factor for RL algorithm

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def trainManualLearner_test():
    import random
    sequence_length = 10
    nn_param = [128, 128]
    params = {
        "batchSize": 64,
        "buffer": 5000,
        "nn": nn_param,
        "sequence_length": sequence_length,  # The number of commands that make of a state
        "number_of_actions": 5,
        "cmd2number_reward": "cmd2number_reward.p",
        "GAMMA": 0.9  # Forgetting.
    }
    ML = ManualLearner(params)
    cmd = "exit"
    while True:
        ML.log_cmd_resulted_from_action(cmd)

def trainManualLearner_on_log(cmds):
    sequence_length = 10
    nn_param = [128, 128]
    params = {
        "batchSize": 64,
        "buffer": 5000,
        "nn": nn_param,
        "sequence_length": sequence_length,  # The number of commands that make of a state
        "number_of_actions": 5,
        "cmd2number_reward": "cmd2number_reward.p",
        "GAMMA": 0.9  # Forgetting.
    }
    ML = ManualLearner(params)
    for cmd in cmds:
        ML.log_cmd_resulted_from_action(cmd)
    return ML.featureExpectations

class ManualLearner:
    def __init__(self,params, policy_name="DefaultPolicy"):
        self.policy_name = policy_name
        self.cmds = 0
        self.state = np.zeros(params['sequence_length'])
        self.state_index = 0

        self.featureExpectations = np.zeros(params['sequence_length'])
        self.Prev = np.zeros(params['sequence_length'])
        if isinstance(params["cmd2number_reward"], str):
            #if string load from file
            self.cmd2number_reward = pickle.load(open(params["cmd2number_reward"],"rb"))
        else:
            # if dictionary
            self.cmd2number_reward = params["cmd2number_reward"]

        # sequence_length specifies the number of commands that form a state
        self.sequence_length = params['sequence_length']
        # number_of_actions specifies the number of possible actions
        self.number_of_actions = params["number_of_actions"]

    def log_cmd_resulted_from_action(self, cmd):
        # Check if the command is known
        if cmd in self.cmd2number_reward:
            cmd_num, reward = self.cmd2number_reward[cmd]
        else:
            cmd_num, reward = self.cmd2number_reward["unknown"]

        self.cmds += 1


        if self.state_index >= 1:
            self.state = np.roll(self.state, -1)
            self.state[self.sequence_length - 1] = cmd_num
            if self.state_index < self.sequence_length:
                self.state_index = self.state_index + 1

            # 56 is the "exit" command
            if cmd == "exit":
                # The state is reset
                self.state = np.zeros(self.sequence_length)
                self.state_index = 0
        else:
            # The state is a sequence of the last params["sequence_length"] commands given
            # Here the first command is inputed into the state
            self.state[self.state_index] = cmd_num
            self.state_index = self.state_index + 1

        if self.cmds > 100:
            self.featureExpectations += (GAMMA ** (self.cmds - 101)) * self.state

        # Tell us something.
        changePercentage = (np.linalg.norm(self.featureExpectations - self.Prev) * 100.0) / float(np.linalg.norm(self.featureExpectations))

        self.Prev = np.array(self.featureExpectations)

        if self.cmds % 2000 == 0:
            try:
                pickle.dump(self.featureExpectations, open("policies/"+self.policy_name+".p","wb"))
            except Exception:
                print(bcolors.WARNING + "Can't save policy.\n Make sure the 'policies' folder exists along with other neccesary folders" + bcolors.ENDC)

if __name__ == "__main__":
    trainManualLearner_test()