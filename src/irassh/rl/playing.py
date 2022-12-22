import numpy as np
import pickle

class play:
    def __init__(self,model, weights, sequence_length=10,cmd2number_reward = "",GAMMA=0.9):
        self.model = model
        self.weights = weights
        self.GAMMA = GAMMA

        self.cmds = 0
        self.state = np.zeros(sequence_length)
        self.state_index = 0

        if isinstance(cmd2number_reward, str):
            #if string load from file
            self.cmd2number_reward = pickle.load(open(cmd2number_reward,"rb"))
        else:
            # if dictionary
            self.cmd2number_reward = cmd2number_reward

        self.featureExpectations = np.zeros(len(weights))
        self.last_reward = None
        self.ready = False

    def get_command(self,cmd):
        # Check if the command is known
        if cmd in self.cmd2number_reward:
            cmd_num, reward = self.cmd2number_reward[cmd]
        else:
            cmd_num, reward = self.cmd2number_reward["unknown"]

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
            self.state[self.state_index] = self.cmd_num
            self.state_index = self.state_index + 1
        self.cmds += 1

        if len(self.state.shape) == 1:
            batch_state = np.expand_dims(self.state, axis=0)
        else:
            batch_state = self.state
        # Choose action.
        action = (np.argmax(self.model.predict(batch_state, batch_size=1)[0]))

        if self.last_reward is not None:
            if self.cmds > 100:
                self.featureExpectations += (self.GAMMA ** (self.cmds - 101)) * np.array(state)
            # print ("Feature Expectations :: ", featureExpectations)
            # Tell us something.
            if self.cmds % 2000 == 0:
                print("Current distance: %d frames." % self.cmds)
                print("featureExpectations ready")
                self.ready = True
        self.last_reward = reward
