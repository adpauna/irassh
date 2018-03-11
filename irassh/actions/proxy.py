import os
import random
import time
import sys

import pygeoip

from irassh.actions import dao
from irassh.rl import rl_state
from irassh.rl.learning import q_learner
from irassh.rl.manual import ManualLearner
from irassh.rl.irl_agent import irlAgent
import numpy as np

import pickle

# generate RL state
sequence_length = 10
nn_param = [128, 128]
params = {
    "batchSize": 64,
    "buffer": 5000,
    "nn": nn_param,
    "sequence_length": 10,  # The number of commands that make of a state
    "number_of_actions": 5,
    "cmd2number_reward":  "irassh/rl/cmd2number_reward.p",
    "GAMMA": 0.9  # Forgetting.
}
rl_agent = q_learner(params)
policy_learner = ManualLearner(params)

#for irl agent
randomPolicyFE = np.random.random_sample(sequence_length)
# This need to be generated in manual.py
expertPolicyFE = np.random.random_sample(sequence_length)
irl_agent = irlAgent(params, randomPolicyFE, expertPolicyFE, num_frames=1100, behavior="DefaultPolicy")

cmd_log = []

class Action(object):
    def __init__(self, write):
        self.is_allowed = True
        self.write = write

    def process(self):
        """
        """

    def isPassed(self):
        return self.is_allowed

    def setPassed(self, passed):
        self.passed = passed

    def write(self, text):
        self.write(text)


class BlockedAction(Action):
    def __init__(self, write):
        super(BlockedAction, self).__init__(write)

        self.setPassed(False)

    def process(self):
        self.write("Blocked command!\n")

    def getActionName(self):
        return "Blocked"

    def getColor(self):
        return "31"


class DelayAction(Action):
    def process(self):
        time.sleep(3)
        self.setPassed(True)
        print("delay ...\n")

    def getActionName(self):
        return "Delay"

    def getColor(self):
        return "34"


class AllowAction(Action):
    def process(self):
        self.setPassed(True)

    def getActionName(self):
        return "Allow"

    def getColor(self):
        return "32"


class InsultAction(Action):
    def __init__(self, clientIp, write):
        super(InsultAction, self).__init__(write)

        self.clientIp = clientIp
        self.setPassed(False)

    def process(self):
        location = self.getCountryCode()
        print("Insult Message! IP= %s/location=%s\n" % (self.clientIp, location))
        self.write(dao.getIRasshDao().getInsultMsg(location.lower()) + "\n")

    def getCountryCode(self):
        path, file = os.path.split(__file__)
        file_name = os.path.join(path, "geo_ip.dat")
        print("Load geo_ip.dat from " + file_name)
        geo_ip = pygeoip.GeoIP(file_name)
        return geo_ip.country_code_by_addr(self.clientIp)

    def getActionName(self):
        return "Insult"

    def getColor(self):
        return "38"


class FakeAction(Action):
    def __init__(self, command, write):
        super(FakeAction, self).__init__(write)

        self.command = command
        self.setPassed(False)

    def process(self):
        fake_output = dao.getIRasshDao().getFakeOutput(self.command)
        if fake_output is not None:
            self.write(fake_output + "\n")

    def getActionName(self):
        return "Fake"

    def getColor(self):
        return "33"


class ActionGenerator(object):
    def generate(self):
        '''
        :return: action
        '''


class RandomActionGenerator(ActionGenerator):
    def generate(self):
        return random.randrange(0, 4)

class ManualActionGenerator(ActionGenerator):
    def generate(self):
        policy_learner.log_cmd_resulted_from_action(rl_state.current_command)
        message = '''
Select manual action:

0 : Allow
1: Block
2: Delay
3: Fake
4: Insult
            '''
        while True:
            if sys.version_info.major >= 3:
                action = input(message)
            else:
                action = raw_input(message)
            try:
                action = int(action)
                if action>-1 and action<5:
                    return action
                else:
                    print("Number not in list")
            except Exception as e:
                print("Please input a number")



class RlActionGenerator(ActionGenerator):
    def generate(self):
        print ("get action by q-learning", rl_state.current_command)
        rl_agent.train(rl_state.current_command)
        return rl_agent.choose_action()

class IrlActionGenerator(ActionGenerator):
    def generate(self):
        print ("get action by from irl agen", rl_state.current_command)
        return irl_agent.choose_action_based_on_command(rl_state.current_command)

class ConstActionGenerator(ActionGenerator):
    def __init__(self, action):
        self.action = action

    def generate(self):
        policy_learner.log_cmd_resulted_from_action(rl_state.current_command)
        return self.action

class FileActionGenerator(ActionGenerator):
    def __init__(self, file):
        self.file = file

    def generate(self):
        cmd_log.append(rl_state.current_command)
        with open("cmd_log.p","wb") as f:
            pickle.dump(cmd_log, f, protocol=0)
        action = -1
        while action==-1:
            if os.path.isfile(self.file):
                with open(self.file,"rb") as f:
                    action = pickle.load(f)
            if action==-1:
                time.sleep(0.5)
        with open(self.file,"wb") as f:
            pickle.dump(-1, f)
        return action

class ActionFactory(object):

    def __init__(self, write, listener, generator):
        self.write = write
        self.listener = listener
        self.generator = generator
        pass

    def getAction(self, cmd, clientIp):
        action = self.generator.generate()
        print("Receive action: ", action)
        self.listener.handle(action)
        if action == 0:
            return AllowAction(self.write)
        elif action == 1:
            return DelayAction(self.write)
        elif action == 2:
            return FakeAction(cmd, self.write)
        elif action == 3:
            return InsultAction(clientIp, self.write)
        elif action == 4:
            return BlockedAction(self.write)


class ActionValidator(object):
    def __init__(self, factory):
        self.factory = factory
        pass

    def validate(self, cmd, clientIp):
        self.action = self.factory.getAction(cmd, clientIp)
        self.action.process()
        return self.action.isPassed()

    def getActionName(self):
        return self.action.getActionName()

    def getActionColor(self):
        return self.action.getColor()


class ActionPersister(object):
    def save(self, actionState, cmd):
        if "initial_cmd" in actionState.keys():
            print("Save next_cmd: " + cmd)
            actionState["next_cmd"] = cmd
            dao.getIRasshDao().saveCase(actionState)

        print("Save initial_cmd: " + cmd)
        actionState["initial_cmd"] = cmd


class ActionListener(object):
    def __init__(self, store):
        self.store = store
        pass

    def handle(self, action):
        self.store["action"] = action
