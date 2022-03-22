#!/usr/bin/python
# coding: utf-8
import sys
import subprocess
import time
from netmiko import Netmiko
from netmiko import ssh_exception

host_ip = '192.168.2.131'
host_user = 'sysadmin'
host_password = 'P@ssw0rd'

name = input("Enter User Name:")

if name == 'root':
                print("Can't do anything with the 'root' user account......")
                print(f"\n{'#' * 50}\nFinished Executing Script\n{'#' * 50}")
                sys.exit()

print(f"\n{'#'*50}\n1. Connecting to the host\n{'#'*50}")
try:
                net_connect = Netmiko(device_type='linux_ssh',host = host_ip,username = host_user,password = host_password)
                print(net_connect.find_prompt())
                print(f"\n{'*'*10}Connected to the host{'*'*10}")
                print(net_connect.find_prompt(),end='')
                net_connect.write_channel(f'cat /etc/passwd | grep ' + name +'\n')
                time.sleep(2)
                output = net_connect.read_channel()
                print(output)
                nameseek = (name + ":")
                if nameseek in output:
                               print("Found user")
                               net_connect.write_channel(f'sudo userdel -r ' + name +'\n')
                               time.sleep(2)
                               output = net_connect.read_channel()
                               print(output)
                               if '[sudo] password' in output:
                                                               print("**Received Password Prompt, Entering password**")
                                                               net_connect.write_channel(host_password+'\n')
                                                               time.sleep(2)
                                                               output = net_connect.read_channel()
                                                               print(output)
                               else:
                                                               print("error")
                else:
                               print ("User not found")

except ssh_exception.AuthenticationException:
                print("Host Auth failed")
except ssh_exception.NetmikoTimeoutException:
                print("Host not reachable")

print(f"\n{'#'*50}\nFinished Executing Script\n{'#'*50}")
sys.exit()