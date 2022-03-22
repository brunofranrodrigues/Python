import os
import json
from pprint import pprint
import netmiko
from netmiko import (
    ConnectHandler,
    NetmikoTimeoutException,
    NetmikoAuthenticationException,
)

path = os.getcwd()
jsonFilePath = os.path.join(path,"files/devices.json")

config_list_cisco_cmd = ['username admin password 0 maxmax','end', 'write memory']

config_list_fortinet_cmd = ['config system admin','edit admin', 'set password maxmax', 'end', 'exit']

with open(jsonFilePath, "r", encoding="utf8") as arquivo:
    conteudo_txt = arquivo.read()
    conteudo_json = json.loads(conteudo_txt)

def send_command(device, commands):
    result = {}
    try:
        with ConnectHandler(**device) as ssh:
            ssh.enable()
            for command in commands:
                output = ssh.send_config_set(command)
                result[command] = output
            return result
    except (NetmikoTimeoutException, NetmikoAuthenticationException) as error:
        print(error)

for device in conteudo_json:
    if device["device_type"] == "fortinet":
        result = send_command(device, config_list_fortinet_cmd)
    elif device["device_type"] == "cisco_ios":
        result = send_command(device, config_list_cisco_cmd)