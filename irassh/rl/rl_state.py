from irassh.rl.learning import q_learner

current_command = None
prev_command = None

current_reward = None

rl_action = None
rl_params = ""

# generate RL state
sequence_length = 10
nn_param = [128, 128]
params = {
    "batchSize": 64,
    "buffer": 5000,
    "nn": nn_param,
    "sequence_length": 10,  # The number of commands that make of a state
    "number_of_actions": 5,
    "cmd2number_reward": "irassh/rl/cmd2number_reward.p",
    "GAMMA": 0.9  # Forgetting.
}
rl_agent = q_learner(params)