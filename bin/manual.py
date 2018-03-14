import time
import fcntl
import os
import signal
import pickle
from os import path
import sys

action_file = "manual/control/receive-action.p"
input_cmd_folder = "manual/input"

current_state = 0

last_cmd = ""

message = '''
Select manual action:

0: Allow
1: Block
2: Delay
3: Fake
4: Insult
'''

def handler(signum, frame):
    action = input(message)
    action = int(action)
    if action > -1 and action < 5:
        with open(action_file, "wb") as af:
            pickle.dump(action, af)
    else:
        print("Action number is incorrect")
        action = input(message)
        action = int(action)

print("Waiting for new command...")

signal.signal(signal.SIGIO, handler)
fd = os.open(input_cmd_folder, os.O_RDONLY)
fcntl.fcntl(fd, fcntl.F_SETSIG, 0)
fcntl.fcntl(fd, fcntl.F_NOTIFY, fcntl.DN_MODIFY)

while True:
    time.sleep(1000)
