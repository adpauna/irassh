import numpy as np
import pickle
from manual import get_cmd_prop
from learning import get_cmd2reward

def weights2cmd2num_reward(weights):
    print weights
    weights = np.sum(weights, axis=0)
    print weights
    cmd2num_reward = dict()
    cmd2prop = get_cmd_prop()
    if len(weights) < 50:
        for cmd in cmd2prop:
            prop = cmd2prop[cmd]
            cmd2num_reward[cmd] = (len(cmd2num_reward)+1, np.sum(np.multiply(prop, weights)))
    else:
        cmd2number_reward_preset = get_cmd2reward()
        for cmd in cmd2number_reward_preset:
            cmd_num = cmd2number_reward_preset[cmd][0]
            cmd2num_reward[cmd] = (cmd_num, weights[cmd_num])
    return cmd2num_reward

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="pickle file that contains the irl output")
    parser.add_argument("output_file", help="output filename (will be a pickle file containing a dictionary from the command to its associated number and its reward")

    args = parser.parse_args()
    if (args.input_file == None or args.output_file == None):
        parser.print_help()
    else:
        with open(args.input_file,"rb") as f:
            weights = pickle.load(f)
        cmd2num_reward = weights2cmd2num_reward(weights)
        with open(args.output_file,"wb") as f:
            pickle.dump(cmd2num_reward, f)