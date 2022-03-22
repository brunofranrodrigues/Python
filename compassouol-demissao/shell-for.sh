#!/bin/bash
for i in `cat list-users.txt` ; do
 python3 ssh_task_check_users.py $i
done;
