import numpy as np
import pickle
from manual import get_cmd_prop
import pandas as pd
#from learning import get_cmd2reward

def get_cmd2reward(filename="Commands.xlsx", save_pickle=True):
    cmd2number_reward = dict()
    xl = pd.ExcelFile(filename)
    '''
    Reward:
        hacker <- 200
        download <- 500
        implemented and not download <- 0
        not implemented and not download <- -200
        "exit" <- -500
    '''
    for sheet_name in xl.sheet_names:
        df = xl.parse(sheet_name)
        if sheet_name == "Hacker":
            for row_index, row in df.iterrows():
                cmd = row["IRASSH commands"].lower()
                cmd2number_reward[cmd] = (len(cmd2number_reward) + 1, 200)
        elif sheet_name == "Linux":
            for row_index, row in df.iterrows():
                cmd = row["IRASSH commands"].lower()
                isImplemented = row["Type_based_on_implementation"]=="implemented in code (real functionality emulated )"
                isDownload    = row["Type_based_on_rl_algo"]=="download"
                reward = 0
                if isDownload:
                    reward = 500
                elif not isImplemented:
                    reward = -200
                cmd2number_reward[cmd] = (len(cmd2number_reward) + 1, reward)

    cmd2number_reward["exit"] = (len(cmd2number_reward) + 1, -500)
    cmd2number_reward["unknown"] =(len(cmd2number_reward) + 1, 0)
    if save_pickle:

        with open("cmd2number_reward.p","wb") as f:
            pickle.dump(cmd2number_reward,f, protocol=0)
    return cmd2number_reward

def weights2cmd2num_reward(weights, cmds_xlsx = "Commands.xlsx"):
    print weights
    weights = np.sum(weights, axis=0)
    print weights
    cmd2num_reward = dict()
    cmd2prop = get_cmd_prop(cmds_xlsx)
    if len(weights) < 50:
        for cmd in cmd2prop:
            prop = cmd2prop[cmd]
            cmd2num_reward[cmd] = (len(cmd2num_reward)+1, np.sum(np.multiply(prop, weights)))
    else:
        cmd2number_reward_preset = get_cmd2reward(cmds_xlsx,False)
        for cmd in cmd2number_reward_preset:
            cmd_num = cmd2number_reward_preset[cmd][0]
            cmd2num_reward[cmd] = (cmd_num, weights[cmd_num])
    return cmd2num_reward

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("input_file", help="pickle file that contains the irl output")
    parser.add_argument("output_file", help="output filename (will be a pickle file containing a dictionary from the command to its associated number and its reward")
    parser.add_argument("commands_xlsx", help="Excel file that describes the commands", default="Commands.xlsx")

    args = parser.parse_args()
    if (args.input_file == None or args.output_file == None):
        parser.print_help()
    else:
        with open(args.input_file,"rb") as f:
            weights = pickle.load(f)
        cmd2num_reward = weights2cmd2num_reward(weights, args.commands_xlsx)
        with open(args.output_file,"wb") as f:
            pickle.dump(cmd2num_reward, f)