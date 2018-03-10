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
import curses  # for keypress
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

class ManualLearner:
    def __init__(self,params, policy_name="DefaultPolicy"):
        self.policy_name = policy_name
        self.cmds = 0
        self.state = np.zeros(params['sequence_length'])

        self.featureExpectations = np.zeros(self.state)
        self.Prev = np.zeros(self.state)
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
            if self.state_index == self.sequence_length:
                # The oldest command is erased and the newest is introduced
                np.roll(self.state, 1)
                self.state[self.sequence_length - 1] = cmd_num
            else:
                # The next command is added to the state
                self.state[self.state_index] = cmd_num
                self.state_index = self.state_index + 1


            # 56 is the "exit" command
            if cmd_num == 56:
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
        changePercentage = (np.linalg.norm(self.featureExpectations - self.Prev) * 100.0) / np.linalg.norm(self.featureExpectations)

        print(self.cmds)
        print("percentage change in Feature expectation ::", changePercentage)
        self.Prev = np.array(self.featureExpectations)

        if self.cmds % 2000 == 0:
            try:
                pickle.dump(self.featureExpectations, open("policies/"+self.policy_name+".p","wb"))
            except Exception:
                print(bcolors.WARNING + "Can't save policy.\n Make sure the 'policies' folder exists along with other neccesary folders" + bcolors.ENDC)

