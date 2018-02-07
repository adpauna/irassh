import time

from irassh.rl import rl_state


def getCommandReward(command):
    l = ["wget", "scp", "ftp", "sftp", "curl", "axel"]
    for c in l:
        if c in command:
            return 0.5
    if command.startswith("./"):
        return 1
    l2 = ["python", "php", "sh", "bash"]
    for c in l2:
        if command.startswith(c):
            return 1
    return 0


def getCommandType(command):
    l = ["wget", "scp", "ftp", "sftp", "curl", "axel"]
    for c in l:
        if c in command:
            return 1
    if command.startswith("./"):
        return 2
    l2 = ["python", "php", "sh", "bash"]
    for c in l2:
        if command.startswith(c):
            return 1
    return 0


def getCurrentCommand():
    # global current_command
    # global current_reward
    # global prev_command
    while True:
        print("get current command -============================", rl_state.current_command)
        if not rl_state.current_command:
            time.sleep(1)
        else:
            rl_state.prev_command = rl_state.current_command
            rl_state.current_command = None
            rl_state.current_reward = getCommandReward(rl_state.prev_command)
            return getCommandType(rl_state.prev_command)


def getCurrentReward():
    return rl_state.current_reward


def doAction(action):
    print("do action ===================================")
    rl_state.rl_action = action
