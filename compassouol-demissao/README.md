# task-resignation
### ssh_task_check_users.py

### HELP
python3 ssh_task_check_users.py -h
usage: ssh_task_check_users.py [-h] [-c check-user] [-d delete-user] [-t task-id]

check/delete users

optional arguments:
  -h, --help            show this help message and exit
  
  -c check-user, --check check-user check if user exists
  
  -d delete-user, --delete delete-user delete the user from the servers
  
  -t task-id, --task task-id Manually specific task ID

### SAMPLE - check-user
run -> python3 ssh_task_check_users.py -c sysadmin


### SAMPLE - delete-user
run -> python3 ssh_task_check_users.py -d huginho -t T203632
