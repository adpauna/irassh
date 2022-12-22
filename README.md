# Fork of the irassh repository - forked to run on docker-compose


This is a fork for the irassh SSH and Telnet Honeypot effort that allows to run
it with docker compose. The docker-compose service will listen on the public system interface on port 22 for live usage.


## Requirements

Software required:

* Python 2.7+, (Python 3 not yet supported due to Twisted dependencies)
* python-virtualenv

For Python dependencies, see requirements.txt

## Files of interest:

* `src/irassh.cfg` - Cowrie's configuration file. Default values can be found in `cowrie.cfg.dist`
* `src/data/fs.pickle` - fake filesystem
* `src/data/userdb.txt` - credentials allowed or disallowed to access the honeypot
* `src/dl/` - files transferred from the attacker to the honeypot are stored here
* `src/honeyfs/` - file contents for the fake filesystem - feel free to copy a real system here or use `bin/fsctl`
* `log/irassh.json` - transaction output in JSON format
* `log/irassh.log` - log/debug output
* `log/tty/*.log` - session logs
* `src/txtcmds/` - file contents for the fake commands
* `bin/createfs` - used to create the fake filesystem
* `bin/playlog` - utility to replay session logs

## How to run
* Create 2 folders: log and log/tty
* `bin/irassh start` - start the server
* `bin/irassh stop` - stop the server
* Start client: `ssh root@localhost`, input any pwd
* Run playlog: `bin/playlog log/tty/[file_name]`

## How to run the inverse reinforcement learning agent
* Step 1: Run bin/irassh start with manual set to True in irassh/shell/honeypot.py and start bin/manual.py to give manual commands
* Step 2: After enough commands have been recorded a file named manual/input/cmd.p should appear. Use this file as an input for irassh/rl/manual.py ( e.g. python manual.py manual/input/cmd.p expertFE.p -p )
* Step 3: Use the policy obtained in the previous step in irassh/actions/proxy.py by setting the value of expertFE to it
* Step 4: Run bin/irassh start with manual set to False and useIRL set to True and input enough commands until the irl agent is trained. The result should be saved in a pickle file named using the behavior attribute of the irl_agent with "-optimal_weight.p" appended to it
* Step 5: Run irassh/rl/policy2reward.py with the output from the previous step to create a pickle file that contains the reward function for the q_learner (i.e. python policy2reward.py DefaultBehavior-optimal_weight.p cmd2number_reward.p
* Step 6: Train a Reinforcement Learning agent by starting irassh with manual and useIRL set to False. Make sure the cmd2number_reward is set correctly in irassh/actions/proxy.py 


## How to setup

Just run sudo docker-compose build && sudo docker-compose up -d

### Test manual mode

* Turn on manual = true in irassh/shell/honeypot.sh
* Turn on server: bin/irassh start
* Turn on manual console: python bin/manual
* Connect to server: ssh root@localhost -p 2222

## New features
* Add action to playlog
* Add action mysql log
* Move all functions from rassh to irassh
