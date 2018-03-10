# IRL algorith developed for the toy car obstacle avoidance problem for testing.
import numpy as np
import logging
from nn import neural_net  # construct the nn and send to playing
from cvxopt import matrix
from cvxopt import solvers  # convex optimization library
import pickle
from learning import q_learner


NUM_STATES = 8
BEHAVIOR = 'red'  # yellow/brown/red/bumping
FRAMES = 100000  # number of RL training frames per iteration of IRL

def trainirlAgent_test():
    import random
    sequence_length = 10
    nn_param = [128, 128]
    params = {
        "batchSize": 64,
        "buffer": 5000,
        "nn": nn_param,
        "sequence_length": 10,  # The number of commands that make of a state
        "number_of_actions": 5,
        "cmd2number_reward": "cmd2number_reward.p",
        "GAMMA": 0.9  # Forgetting.
    }
    randomPolicyFE = np.random.random_sample(sequence_length)

    #This need to be generated in manual.py
    expertPolicyFE = np.random.random_sample(sequence_length)

    irl_agent = irlAgent(params, randomPolicyFE, expertPolicyFE, num_frames=1100, behavior="DefaultPolicy")
    rawcmd = ""
    while not irl_agent.weights_found:
        action = irl_agent.choose_action_based_on_command(rawcmd)
    return irl_agent.optimal_weights


class irlAgent:
    def __init__(self, params, randomFE, expertFE, epsilon=0.1, num_frames=5000, behavior="DefaultPolicy", play_commands=2000):
        self.play_commands = play_commands
        self.params = params

        if isinstance(params["cmd2number_reward"], str):
            #if string load from file
            self.cmd2number_reward = pickle.load(open(params["cmd2number_reward"],"rb"))
        else:
            # if dictionary
            self.cmd2number_reward = params["cmd2number_reward"]

        self.sequence_length = params["sequence_length"]
        self.number_of_actions = params["number_of_actions"]
        self.randomPolicy = randomFE
        self.expertPolicy = expertFE
        self.num_frames = num_frames
        self.behavior = behavior
        self.epsilon = epsilon  # termination when t<0.1
        self.randomT = np.linalg.norm(
            np.asarray(self.expertPolicy) - np.asarray(self.randomPolicy))  # norm of the diff in expert and random
        self.policiesFE = {
            self.randomT: self.randomPolicy}  # storing the policies and their respective t values in a dictionary
        print("Expert - Random at the Start (t) :: ", self.randomT)
        self.currentT = self.randomT
        self.minimumT = self.randomT
        self.weights_found = False
        self.optimalWeightFinderStart()


    def policyListUpdater_start(self, W):
        # add the policyFE list and differences
        self.current_function_state = "play"
        self.IRL_helper_start(W, self.behavior, self.num_frames)

    def IRL_helper_start(self,W, behavior, num_frames):
        self.W = W
        self.rl_agent = q_learner(self.params, save_every= self.num_frames*2)
        self.train_agent_frames = 0
        self.current_function_state = "train_rl_agent"

    def policyListUpdater_getRLAgentFE(self,model):
        self.play(model, self.W, self.params["GAMMA"])  # return feature expectations by executing the learned policy


    def policyListUpdater_end(self, tempFE):
        hyperDistance = np.abs(np.dot(self.W, np.asarray(self.expertPolicy) - np.asarray(tempFE)))  # hyperdistance = t
        self.policiesFE[hyperDistance] = tempFE
        self.optimalWeightFinderStep(hyperDistance, self.W)

    def optimalWeightFinderStart(self):
        self.f = open('weights-' + BEHAVIOR + '.txt', 'w')
        self.i = 1
        W = self.optimization()  # optimize to find new weights in the list of policies
        print("weights ::", W)
        self.f.write(str(W))
        self.f.write('\n')
        print("the distances  ::", self.policiesFE.keys())
        self.policyListUpdater_start(W)

    def optimalWeightFinderStep(self, currentT, W):
        if currentT <= self.epsilon:
            print("Current distance (t) is:: ", self.currentT)
            print("Found optimal weight")
            self.weights_found = True
            self.optimal_weights = W
            pickle.dump(W, open(self.behavior + "-optimal_weight.p","wb"))
        self.i += 1
        W = self.optimization()  # optimize to find new weights in the list of policies
        print("weights ::", W)
        self.f.write(str(W))
        self.f.write('\n')
        self.policyListUpdater_start(W)
        print("the distances  ::", self.policiesFE.keys())


    def optimization(self):  # implement the convex optimization, posed as an SVM problem
        m = len(self.expertPolicy)
        P = matrix(2.0 * np.eye(m), tc='d')  # min ||w||
        q = matrix(np.zeros(m), tc='d')
        policyList = [self.expertPolicy]
        h_list = [1]
        for i in self.policiesFE.keys():
            policyList.append(self.policiesFE[i])
            h_list.append(1)
        policyMat = np.matrix(policyList)
        policyMat[0] = -1 * policyMat[0]
        G = matrix(policyMat, tc='d')
        h = matrix(-np.array(h_list), tc='d')
        sol = solvers.qp(P, q, G, h)

        weights = np.squeeze(np.asarray(sol['x']))
        norm = np.linalg.norm(weights)
        weights = weights / norm
        return weights  # return the normalized weights

    def choose_action_play(self,cmd):
        self.play_cmds += 1
        self.play_state, self.play_state_index, immediateReward = self.update_state(self.play_state, self.play_state_index, cmd)

        if len(self.play_state.shape) == 1:
            state = np.expand_dims(self.play_state, axis=0)
        else:
            state = self.play_state
        # Choose action.
        action = (np.argmax(self.play_model.predict(state, batch_size=1)[0]))

        if self.play_cmds > 100:
            self.play_featureExpectations += (self.play_GAMMA ** (self.play_cmds - 101)) * np.array(self.play_state)
        # print ("Feature Expectations :: ", featureExpectations)
        # Tell us something.
        return action


    def play(self, model, weights, GAMMA):
        self.play_state = np.zeros(self.sequence_length)
        self.play_state_index = 0
        self.play_featureExpectations = np.zeros(len(weights))
        self.play_cmds = 0
        self.current_function_state = "play"
        self.play_model = model
        self.play_GAMMA = GAMMA

    def choose_action_based_on_command(self,cmd):
        if self.current_function_state == "play":
            action = self.choose_action_play(cmd)
            if self.play_cmds%100 == 0:
                print(self.current_function_state,self.play_cmds)
            if self.play_cmds % self.play_commands == 0:
                self.policyListUpdater_end(self.play_featureExpectations)
        elif self.current_function_state == "train_rl_agent":
            self.rl_agent.train(cmd)
            action = self.rl_agent.choose_action()
            self.train_agent_frames += 1
            if self.train_agent_frames%100 == 0:
                print(self.current_function_state,self.train_agent_frames)
            if self.train_agent_frames > self.num_frames:
                self.policyListUpdater_getRLAgentFE(self.rl_agent.model)
        else:
            print("Error")

        return action

    def update_state(self, state, state_index, cmd):
        cmd = cmd.lower()
        # Check if the command is known
        if cmd in self.cmd2number_reward:
            cmd_num, reward = self.cmd2number_reward[cmd]
        else:
            cmd_num, reward = self.cmd2number_reward["unknown"]


        if state_index >= 1:
            np.roll(self.state, 1)
            self.state[self.sequence_length - 1] = cmd_num
            if self.state_index < self.sequence_length:
                self.state_index = self.state_index + 1


            # 56 is the "exit" command
            if cmd == "exit":
                # The state is reset
                state = np.zeros(self.sequence_length)
                state_index = 0
        else:
            # The state is a sequence of the last params["sequence_length"] commands given
            # Here the first command is inputed into the state
            state[state_index] = cmd_num
            state_index = state_index + 1

        return state, state_index, reward

if __name__ == '__main__':
    trainirlAgent_test()
