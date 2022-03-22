#!/usr/bin/python
# coding: utf-8
#Criado em 15/12/2021
#Autor: Bruno Rodrigues
import argparse
import json
import os
import sys
import time
from datetime import datetime
from netmiko import Netmiko
from netmiko import ssh_exception

data_e_hora_atuais = datetime.now()
data_e_hora_em_texto = data_e_hora_atuais.strftime('%d/%m/%Y %H:%M:%S')

scriptname = sys.argv[0]

try:
    arg = sys.argv[1]
except IndexError:
    raise SystemExit(f'Usage: python3 ' + scriptname + ' -h')

parser = argparse.ArgumentParser(description='check hosts')
parser.add_argument('-c', '--check', metavar='check-hosts', help='check servers for vulnerability', dest='host')

args = parser.parse_args()
hosts = args.host

### variavies globais
dirLog = os.getcwd()

# Check for Log4j
# comando para validar Log4j

cmd_sudo = (f'sudo su -l\n')
check_Log4j = (f'for f in $(lsof | grep ".jar" | awk \'{{print $NF}}\'); do VULNERABLE=$(unzip -l "$f" 2>/dev/null | grep -F JndiManager.class); if [ $? -eq 0 ];then BUNDLE_VERSION=$(unzip -p "$f" 2>/dev/null | grep Bundle-Version | awk \'{{print $NF}}\'); RELEASE=$(echo ${{BUNDLE_VERSION}} | cut -d"." -f 1); MAJOR=$(echo ${{BUNDLE_VERSION}} | cut -d"." -f 2); if [ "${{RELEASE}}" -eq 2 -a "${{MAJOR}}" -lt 15 ];then echo "VULNERABLE"; break; fi; fi; done\n')

path = os.getcwd()
jsonFilePath = os.path.join(path, "devices.json")

with open(jsonFilePath, "r", encoding="utf8") as arquivo:
    conteudo_txt = arquivo.read()
    conteudo_json = json.loads(conteudo_txt)

def eventlog(filename, log):
    type_file = '.logs'
    file_name = filename + type_file
    filePath = os.path.join(dirLog, file_name)
    if os.path.exists(filePath):
        outlog = open(filePath, 'a', encoding='utf8')
        outlog.write(data_e_hora_em_texto)
        outlog.write(' | ')
        outlog.write(log)
        outlog.write('\n')
        outlog.close()
    else:
        print("Criado o log {}".format(file_name))
        outlog = open(filePath, 'w', encoding='utf8')
        outlog.write(data_e_hora_em_texto)
        outlog.write(' | ')
        outlog.write(log)
        outlog.write('\n')
        outlog.close()

def connect_jump(device, command):
    device_IP = device['ip']
    jump_server = {
        "device_type": "linux_ssh",
        "ip": "192.168.2.10",
        "username": "root",
        "password": "P@ssw0rd"
    }

    host_user = device['username']
    host_password = device['password']
    host_ip = device['ip']

    result = {}
    try:
        net_connect = Netmiko(**jump_server)
        print("\n**Connected to the jumbox**")
        evento01 = ("**Connected to the jumbox**")
        print(net_connect.find_prompt())
        eventlog(host_ip, evento01)
        eventlog(host_ip, net_connect.find_prompt())
        time.sleep(2)
        print("\n**Connected to the host {}**".format(device_IP))
        evento02 = ("**Connected to the host {}**".format(device_IP))
        eventlog(host_ip, evento02)
        net_connect.write_channel(f'ssh ' + host_user + '@' + host_ip + '\n')
        time.sleep(2)
        output = net_connect.read_channel()
        eventlog(host_ip, output)
        print(output)
        if 'password' in output:
            print("**Received Password Prompt, Entering password**")
            net_connect.write_channel(host_password + '\n')
            time.sleep(2)
            print(f"\n{'#' * 10}\nDestination Device Prompt\n{'#' * 10}")
            print(net_connect.find_prompt())
            net_connect.write_channel(command)
            time.sleep(2)
            output = net_connect.read_channel()
            eventlog(host_ip, output)
            if '[sudo] password' or 'Password:' or 'password:' in output:
                print("**Received Password Prompt, Entering password**")
                net_connect.write_channel(host_password + '\n')
                time.sleep(2)
                output = net_connect.read_channel()
                eventlog(host_ip, output)
            else:
                print("sudo incorrect password")
                erroSUDO = "sudo incorrect password"
                eventlog(host_ip, erroSUDO)
        else:
            print("Unable to get output from the end device")
        result = output
        return result
    except (ssh_exception.NetmikoTimeoutException, ssh_exception.AuthenticationException) as error:
        print(error)

def ssh_send_cmd(device, command):
    result = {}
    try:
        net_connect = Netmiko(**device)
        device_IP = device['ip']
        host_password = device['password']
        print("\n**Connected to the host {}**".format(device_IP))
        evento01 = ("**Connected to the host {}**".format(device_IP))
        eventlog(device_IP, evento01)
        print(net_connect.find_prompt())
        eventlog(device_IP, net_connect.find_prompt())
        net_connect.write_channel(command)
        # eventlog(filename, command)
        time.sleep(2)
        output = net_connect.read_channel()
        eventlog(device_IP, output)
        if '[sudo] password' or 'Password:' or 'password:' in output:
            print("**Received Password Prompt, Entering password**")
            net_connect.write_channel(host_password + '\n')
            time.sleep(2)
            output = net_connect.read_channel()
            eventlog(device_IP, output)
        else:
            print("sudo incorrect password")
            erroSUDO = "sudo incorrect password"
            eventlog(device_IP, erroSUDO)
        print(output)
        result = output
        return result
    except (ssh_exception.NetmikoTimeoutException, ssh_exception.AuthenticationException) as error:
        print(error)

def main():
       for device in conteudo_json:
            if device["ip"] == "10.10.10.10":
                result = connect_jump(device, cmd_sudo)
                result = connect_jump(device, check_Log4j)
            else:
                result = ssh_send_cmd(device, cmd_sudo)
                result = ssh_send_cmd(device, check_Log4j)
       print(f"\n{'#' * 50}\nFinished Executing Script\n{'#' * 50}")
       sys.exit()

if __name__ == '__main__': main()
