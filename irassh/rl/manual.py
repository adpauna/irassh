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
import pickle
import pandas as pd

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
    cmd2prop = get_cmd_prop()
    ML = ManualLearner(params)
    cmd = "exit"
    while True:
        ML.log_cmd_resulted_from_action(cmd)

def trainManualLearner_on_log(cmds, sequence_length = 10, cmd2prop=None, oneHot=False):
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

    ML = ManualLearner(params, cmd2props=cmd2prop,oneHot=oneHot)
    for cmd in cmds:
        ML.log_cmd_resulted_from_action(cmd)
    return ML.featureExpectations


# cmd_prop = [isImplemented, isLinux, isDownload, isHacker, ]
def get_cmd_prop(filename="Commands.xlsx"):
    cmd2prop = dict()
    xl = pd.ExcelFile(filename)

    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)
        if sheet_name == "Hacker":
            for row_index, row in df.iterrows():
                cmd = row["IRASSH commands"].lower()
                cmd2prop[cmd] = np.array([1,0,0,0])
        elif sheet_name == "Linux":
            for row_index, row in df.iterrows():
                cmd = row["IRASSH commands"].lower()
                isImplemented = row["Type_based_on_implementation"]=="implemented in code (real functionality emulated )"
                isDownload    = row["Type_based_on_rl_algo"]=="download"
                state = np.zeros(4)
                state[1] = 1
                if isDownload:
                    state[2] = 1
                if isImplemented:
                    state[0] = 1
                cmd2prop[cmd] = state
    cmd2prop["exit"]    = np.zeros(4)
    cmd2prop["unknown"] = np.zeros(4)
    return cmd2prop

# cmd2props superceeds oneHot
class ManualLearner:
    def __init__(self,params, policy_name="DefaultPolicy", cmd2props = None, oneHot = False):
        self.policy_name = policy_name
        self.cmds = 0
        self.state = np.zeros(params['sequence_length'], dtype=np.int32)
        self.state_index = 0
        self.oneHot = oneHot

        # sequence_length specifies the number of commands that form a state
        self.sequence_length = params['sequence_length']
        # number_of_actions specifies the number of possible actions
        self.number_of_actions = params["number_of_actions"]

        if isinstance(params["cmd2number_reward"], str):
            #if string load from file
            self.cmd2number_reward = pickle.load(open(params["cmd2number_reward"],"rb"))
        else:
            # if dictionary
            self.cmd2number_reward = params["cmd2number_reward"]

        if cmd2props is not None:
            self.cmd2props = dict()

            self.number_of_props = 0
            for cmd in self.cmd2number_reward:
                cmd_num = self.cmd2number_reward[cmd][0]
                self.cmd2props[cmd_num] = cmd2props[cmd]
                self.number_of_props = len(cmd2props[cmd])
            if 0 not in self.cmd2props:
                self.cmd2props[0] = np.zeros(self.number_of_props)

            self.featureExpectations = np.zeros((self.sequence_length, self.number_of_props))
            self.Prev = np.zeros((self.sequence_length, self.number_of_props))
        elif oneHot:
            self.cmd2props = None
            number_of_commands = 0
            for cmd in self.cmd2number_reward:
                cmd_num = self.cmd2number_reward[cmd][0]
                if cmd_num > number_of_commands:
                    number_of_commands = cmd_num
            number_of_commands += 1
            self.featureExpectations = np.zeros((self.sequence_length, number_of_commands))
            self.Prev = np.zeros((self.sequence_length, number_of_commands))
        else:
            self.cmd2props = None
            self.featureExpectations = np.zeros(self.sequence_length)
            self.Prev = np.zeros(self.sequence_length)


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
                self.state = np.zeros(self.sequence_length, dtype=np.int32)
                self.state_index = 0
        else:
            # The state is a sequence of the last params["sequence_length"] commands given
            # Here the first command is inputed into the state
            self.state[self.state_index] = cmd_num
            self.state_index = self.state_index + 1


        if self.cmds > 100:
            if self.cmd2props is not None:
                self.prop_state = np.zeros((self.sequence_length, self.number_of_props))
                for i, cmd_num in enumerate(self.state):
                    self.prop_state[i] = self.cmd2props[int(cmd_num)]
                self.featureExpectations += (GAMMA ** (self.cmds - 101)) * self.prop_state
            elif self.oneHot:
                self.oneHot_state = np.zeros(self.featureExpectations.shape)
                self.oneHot_state[np.arange(self.featureExpectations.shape[0]), self.state] = 1
                self.featureExpectations += (GAMMA ** (self.cmds - 101)) * self.oneHot_state
            else:
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
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="pickle file that contains the log of commands")
    parser.add_argument("output_file", help="output filename (will be a pickle file containing a policy")
    parser.add_argument("sequence_length", help="number of commands that define a state", type=int,default=1)
    parser.add_argument("-p","--use_properties", help="use properties representation",action="store_true")
    parser.add_argument("-oh","--use_one_hot", help="use one hot representation",action="store_true")

    args = parser.parse_args()
    if (args.input_file == None or args.output_file == None):
        parser.print_help()
    else:
        with open(args.input_file,"rb") as f:
            cmd_log = pickle.load(f)
        if args.use_properties:
            cmd2prop = get_cmd_prop()
        else:
            cmd2prop = None
        fe = trainManualLearner_on_log(cmd_log, sequence_length=args.sequence_length, cmd2prop=cmd2prop, oneHot=args.use_one_hot)
        print("Resulted Feature expectations:")
        print(fe)
        with open(args.output_file,"wb") as f:
            pickle.dump(fe, f)
