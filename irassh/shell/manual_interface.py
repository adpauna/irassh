import pickle
from os import path
import sys
action_file = "irassh/shell/action.p"
cmd_file = "irassh/shell/cmd.p"

current_state = 0

last_cmd = ""

message = '''
Select manual action:

0 : Allow
1: Block
2: Delay
3: Fake
4: Insult
'''

while True:
    cmd = ""
    if path.isfile(cmd_file):
        with open(cmd_file, "rb") as f:
            cmd_candidate = pickle.load(f)
        if cmd_candidate != "":
            print("New command entered: "+cmd_candidate)

            while True:
                if sys.version_info.major >= 3:
                    action = input(message)
                else:
                    action = raw_input(message)
                try:
                    action = int(action)
                    if action > -1 and action < 5:
                        with open(action_file, "wb") as f:
                            pickle.dump(action, f)
                        break
                    else:
                        print("Number not in list")
                except Exception as e:
                    print("Please input a number")
            with open(cmd_file, "wb") as f:
                pickle.dump("", f)