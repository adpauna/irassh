import numpy as np
import random
import csv
from nn import neural_net, LossHistory
import os.path
import timeit
import os
import pickle

global_sequence_length = 10 # numarul de comenzi ce formeaza o stare
GAMMA = 0.9  # Forgetting.
TUNING = False  # If False, just use arbitrary, pre-selected params.

#ia comanda ca text si returneaza comanda ca numar si reconpensa asociata
def get_command_reward(cmd2number,cmd2reward,dummy=True):
    if dummy:
        # generare comanda random
        cmd_num = random.randint(1, 57)
        #56 e commanda exit
        if cmd_num == 56:
            #resetez starea
            state = np.zeros(params["sequence_length"])
            state_index = 0
            state[0]=cmd_num

        #aflu reconpensa pentru comanda
        reward = cmd2reward[cmd_num]
    else:
        cmd = get_command_as_str()
        #verific daca e o comanda cunoscuta
        if cmd in cmd2number:
            cmd_num = cmd2number[cmd]
            reward  = cmd2reward[cmd_num]
        else:
            cmd_num = cmd2number["unknown"]
            reward  = cmd2reward["unknown"]
    return cmd_num, reward

def do_action(action,dummy=True):
    if not dummy:
        execute_response(action2text[action])

#exemplu pentru params
sequence_length = 10
nn_param = [128, 128]
params = {
    "batchSize": 64,
    "buffer": 5000,
    "nn": nn_param,
    "sequence_length": global_sequence_length,
    "number_of_actions": 5
}

#functie dummy pentru antrenare
def train_net_test(params):
    cmd2reward, cmd2number = get_cmd2reward()
    rl_agent = q_learner(params)
    state = np.zeros(params["sequence_length"])
    state_index = 0

    #generare comanda random
    cmd = random.randint(0, 58)

    #prima comanda din stare
    state[state_index] = cmd
    state_index = state_index + 1
    for i in range(10000):
        action = rl_agent.choose_action(state)
        do_action(action)
        cmd, reward = get_command_reward(cmd2number,cmd2reward)

        if state_index == params["sequence_length"]:
            # scot cea mai veche comanda din stare si o adaug pe cea mai noua
            np.roll(state,1)
            state[params["sequence_length"]-1] = cmd
        else:
            #adaug comanda la stare
            state[state_index] = cmd
            state_index = state_index + 1
        rl_agent.update_replay(reward, state)
    rl_agent.log_results()

#functie dummy pentru play
def playing_test(params):
    cmd2reward, cmd2number = get_cmd2reward()
    rl_agent = q_learner(params)
    state = np.zeros(params["sequence_length"])
    state_index = 0

    #generare comanda random
    cmd = random.randint(0, 58)

    #prima comanda din stare
    state[state_index] = cmd
    state_index = state_index + 1
    while True:
        action = rl_agent.nn_choose_action(state)
        # generare comanda random
        cmd = random.randint(1, 57)
        #56 e commanda exit
        if cmd == 56:
            #resetez starea
            state = np.zeros(params["sequence_length"])
            state_index = 0
            state[0]=cmd

        #aflu reconpensa pentru comanda
        reward = cmd2reward[cmd]

        if state_index == params["sequence_length"]:
            # scot cea mai veche comanda din stare si o adaug pe cea mai noua
            np.roll(state,1)
            state[params["sequence_length"]-1] = cmd
        else:
            #adaug comanda la stare
            state[state_index] = cmd
            state_index = state_index + 1

class q_learner:
    def __init__(self, params, load_replay_file=None, save_replay_file_prefix="replay", save_model_file_prefix="saved-models/", save_every=250, end_value=-500):
        #salvez valorile ca să le pot acesa in alte functii ale clasei

        # aici se specifica numarul de comenzi ce defineste o stare
        self.sequence_length = params['sequence_length']
        # aici se specifica numarul de actiuni posibile
        self.number_of_actions = params["number_of_actions"]
        # construiesc reteaua
        self.model = neural_net(self.sequence_length, self.number_of_actions, params["nn"])
        #generez un nume pentru fisier la salvare
        self.filename = params_to_filename(params)
        #numarul de intrari in replay necesar sa salveze
        self.save_every = save_every
        # denumire pentru fisierul de replay cand este salvat
        self.save_replay_file_prefix = save_replay_file_prefix
        self.save_model_file_prefix = save_model_file_prefix
        # valoarea la terminarea 'jocului'
        self.end_value = end_value
        
        self.observe = 1000  # Number of frames to observe before training.
        self.epsilon = 1     # Chance to choose random action
        self.train_frames = 10000  # Number of frames to play.
        self.batchSize = params['batchSize']
        self.buffer = params['buffer']


        # Just stuff used below.
        self.max_hacker_cmds = 0
        self.hacker_cmds = 0
        self.t = 0
        self.data_collect = []
        if load_replay_file is None:
            self.replay = []  # stores tuples of (S, A, R, S').
        else:
            self.replay = pickle.load(open(load_replay_file, "rb"))

        self.loss_log = []

        # Let's time it.
        self.start_time = timeit.default_timer()
        self.state = np.zeros(10)
        self.lastAction = 0

    def load_model(self, filename):
        self.model =  neural_net(self.sequence_length, self.number_of_actions, params["nn"],filename)

    def choose_action(self, state):
        if len(state.shape)==1:
            state= np.expand_dims(state, axis=0)
        self.t += 1
        self.hacker_cmds += 1

        # Choose an action.
        if random.random() < self.epsilon or self.t < self.observe:
            action = np.random.randint(0, self.number_of_actions)  # random
        else:
            # Get Q values for each action.
            qval = self.model.predict(state, batch_size=1)
            action = (np.argmax(qval))  # best
        self.lastAction = action
        return action

    def nn_choose_action(self, state):
        if len(state.shape)==1:
            state= np.expand_dims(state, axis=0)
        qval = self.model.predict(state, batch_size=1)
        action = (np.argmax(qval))
        return action

    def update_replay(self, reward, new_state, action=None):
        if action is None:
            action = self.lastAction
        
        # Experience replay storage.
        self.replay.append((np.copy(self.state), action, reward, np.copy(new_state)))

        # If we're done observing, start training.
        if self.t > self.observe:
            # If we've stored enough in our buffer, pop the oldest.
            if len(self.replay) > self.buffer:
                self.replay.pop(0)

            # Randomly sample our experience replay memory
            minibatch = random.sample(self.replay, self.batchSize)

            # Get training values.
            X_train, y_train = process_minibatch2(minibatch, self.model, self.sequence_length, self.end_value)

            # Train the model on this batch.
            history = LossHistory()
            self.model.fit(
                X_train, y_train, batch_size=self.batchSize,
                nb_epoch=1, verbose=0, callbacks=[history]
            )
            self.loss_log.append(history.losses)

        # Update the starting state with S'.
        self.state = new_state

        # Decrement epsilon over time.
        if self.epsilon > 0.1 and self.t > self.observe:
            self.epsilon -= (1.0/self.train_frames)

        # We died, so update stuff.
        if reward == -500:
            # Log the car's distance at this T.
            self.data_collect.append([self.t, self.hacker_cmds])

            # Update max.
            if self.hacker_cmds > self.max_hacker_cmds:
                self.max_hacker_cmds = self.hacker_cmds

            # Time it.
            tot_time = timeit.default_timer() - self.start_time
            fps = self.hacker_cmds / tot_time

            # Output some stuff so we can watch.
            print("Max: %d at %d\tepsilon %f\t(%d)\t%f fps" %
                  ( self.max_hacker_cmds, self.t, self.epsilon, self.hacker_cmds, fps))

            # Reset.
            self.hacker_cmds = 0
            start_time = timeit.default_timer()

        # Save the model every 25,000 frames.
        if self.t % self.save_every == 0:
            pickle._dump(self.replay, open(self.save_replay_file_prefix + "-" + str(self.t),"wb"))
            model_save_filename = self.save_model_file_prefix + self.filename + '-' + str(self.t) + '.h5'
            self.model.save_weights(model_save_filename,
                               overwrite=True)
            print("Saving model %s - %d" % (self.filename, self.t))

    def log_results(self):
        # Log results after we're done all frames.
        log_results(self.filename, self.data_collect, self.loss_log)

#in cmd2type.p am salvat un dictionar cu comenzile ca chei si tipurile ca valoare
def get_cmd2reward(filename="cmd2type.p"):
    cmd2type = pickle.load(open(filename, "rb"))
    cmd2number = dict()
    cmd2reward = dict()
    for cmd in cmd2type:
        cmd2number[cmd] = (len(cmd2number) + 1)
        if cmd2type[cmd][1] == 'general':
            cmd2reward[cmd2number[cmd]] = 0
        else:
            cmd2reward[cmd2number[cmd]] = 500
    cmd2number["exit"] = (len(cmd2number) + 1)
    cmd2reward[cmd2number["exit"]] = -500
    cmd2number["unknown"] = (len(cmd2number) + 1)
    cmd2reward[cmd2number["unknown"]] = 0
    return cmd2reward, cmd2number


def log_results(filename, data_collect, loss_log):
    # Save the results to a file so we can graph it later.
    with open('results/sonar-frames/learn_data-' + filename + '.csv', 'w') as data_dump:
        wr = csv.writer(data_dump)
        wr.writerows(data_collect)

    with open('results/sonar-frames/loss_data-' + filename + '.csv', 'w') as lf:
        wr = csv.writer(lf)
        for loss_item in loss_log:
            wr.writerow(loss_item)

def process_minibatch2(minibatch, model,sequence_length ,end_value):
    # by Microos, improve this batch processing function 
    #   and gain 50~60x faster speed (tested on GTX 1080)
    #   significantly increase the training FPS
    
    # instead of feeding data to the model one by one, 
    #   feed the whole batch is much more efficient

    mb_len = len(minibatch)

    old_states = np.zeros(shape=(mb_len, sequence_length))
    actions = np.zeros(shape=(mb_len,))
    rewards = np.zeros(shape=(mb_len,))
    new_states = np.zeros(shape=(mb_len, sequence_length))

    for i, m in enumerate(minibatch):
        old_state_m, action_m, reward_m, new_state_m = m
        old_states[i, :] = old_state_m[...]
        actions[i] = action_m
        rewards[i] = reward_m
        new_states[i, :] = new_state_m[...]

    old_qvals = model.predict(old_states, batch_size=mb_len)
    new_qvals = model.predict(new_states, batch_size=mb_len)

    maxQs = np.max(new_qvals, axis=1)
    y = old_qvals
    non_term_inds = np.where(rewards != end_value)[0]
    term_inds = np.where(rewards == end_value)[0]

    y[non_term_inds, actions[non_term_inds].astype(int)] = rewards[non_term_inds] + (GAMMA * maxQs[non_term_inds])
    y[term_inds, actions[term_inds].astype(int)] = rewards[term_inds]

    X_train = old_states
    y_train = y
    return X_train, y_train

def process_minibatch(minibatch, model, number_of_actions, end_value):
    """This does the heavy lifting, aka, the training. It's super jacked."""
    global global_sequence_length
    X_train = []
    y_train = []
    # Loop through our batch and create arrays for X and y
    # so that we can fit our model at every step.
    for memory in minibatch:
        # Get stored values.
        old_state_m, action_m, reward_m, new_state_m = memory
        # Get prediction on old state.
        old_qval = model.predict(old_state_m, batch_size=1)
        # Get prediction on new state.
        newQ = model.predict(new_state_m, batch_size=1)
        # Get our predicted best move.
        maxQ = np.max(newQ)
        y = np.zeros((1, number_of_actions))
        y[:] = old_qval[:]
        # Check for terminal state.
        if reward_m != end_value:  # non-terminal state
            update = (reward_m + (GAMMA * maxQ))
        else:  # terminal state
            update = reward_m
        # Update the value for the action we took.
        y[0][action_m] = update
        X_train.append(old_state_m.reshape(sequence_length,))
        y_train.append(y.reshape(number_of_actions,))

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    return X_train, y_train

#genereaza un nume pentru fisierul ce trebuie salvat
def params_to_filename(params):
    return str(params['nn'][0]) + '-' + str(params['nn'][1]) + '-' + \
            str(params['batchSize']) + '-' + str(params['buffer'])






if __name__ == "__main__":
    if TUNING:
        #aici se incearca parametri diferiti pentru reteaua neuronala
        param_list = []
        #aici se specifica numarul de comenzi ce defineste o stare
        sequence_lengths = [3,5,10,20]
        #reteau are doua straturi primul numar din fiecare sublista indica numarul de neuroni din primul strat
        #iar al doilea numarul de neuroni din al doilea strat
        nn_params = [[164, 150], [256, 256],
                     [512, 512], [1000, 1000]]
        #numarul de intrari care intra pentru o rulare de Backpropagation
        batchSizes = [40, 100, 400]
        #numarul maxim de comenzi impreuna cu actiunile luate si reconpensele acordate ce vor fi pastrate
        buffers = [10000, 50000]

        #se intorduc toate combinatiile de parametrii specificati mai sus intr-o lista
        for nn_param in nn_params:
            for batchSize in batchSizes:
                for buffer in buffers:
                    for sequence_length in sequence_lengths:
                        params = {
                            "batchSize": batchSize,
                            "buffer": buffer,
                            "nn": nn_param,
                            "sequence_length": sequence_length,
                            "number_of_actions":5
                        }
                        param_list.append(params)

        #se antreneaza reteaua neuronala cu fiecare combinatie din lista
        for param_set in param_list:
            train_net_test(param_set)

    else:

        #aici se foloseste un singur set de parametri pentru antrenare
        nn_param = [128, 128]
        params = {
            "batchSize": 64,
            "buffer": 5000,
            "nn": nn_param,
            "sequence_length": global_sequence_length,
            "number_of_actions": 5
        }
        train_net_test(params)

