#!/usr/bin/python
# coding: utf-8
#Criado em 12/11/2021
#Autor: Bruno Rodrigues
import argparse
import json
import os
import re
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

parser = argparse.ArgumentParser(description='check/delete users')
parser.add_argument('-c', '--check', metavar='check-user', help='check if user exists', dest='user')
parser.add_argument('-d', '--delete', metavar='delete-user', help='delete the user from the servers', dest='deluser')
parser.add_argument('-t', '--task', metavar='task-id', help='Manually specific task ID', dest='task')

args = parser.parse_args()
username = args.user
delusername = args.deluser
tasknumber = args.task

def input_validation():
    if args.deluser == None:
        if not re.match('[_a-z][-0-9_a-z]*', args.user):
            # sys.stderr.write("USER NAME FORMAT NOT VALID")
            raise SystemExit("User Name Format is not Valid")
        if args.user == 'root':
            raise SystemExit("Can't do anything with the 'root' user account......")
    else:
        if not re.match('[_a-z][-0-9_a-z]*', args.deluser):
            # sys.stderr.write("USER NAME FORMAT NOT VALID")
            raise SystemExit("User Name Format is not Valid")
        if not re.match('[tT]{1}\d{6}', args.task):
            raise SystemExit("Task ID Format is not Valid")
        if args.deluser == 'root':
            raise SystemExit("Can't do anything with the 'root' user account......")

### variavies globais
dirLog = os.getcwd()

if args.deluser == None:
    # Genericos do sistema operacional
    # comando para validar usuarios no /etc/passwd
    check_users_passwd = (f'if sudo cat /etc/passwd | grep -w ' + username + ' > /dev/null; then echo "Found  ' + username + '"; else echo "Not Found"; fi\n')
    # comando para validar usuarios no /etc/sudoers
    check_users_sudoers = (f'if sudo cat /etc/sudoers | grep -w ' + username + ' > /dev/null; then echo "Found ' + username + '"; else echo "Not Found"; fi\n')
    # comando para validar usuarios no /etc/ssh/sshd_config
    check_users_sshd = (f'if sudo cat /etc/ssh/sshd_config | grep -w ' + username + ' > /dev/null; then echo "Found ' + username + '"; else echo "Not Found"; fi\n')
    # TACACs UOLHOST
    # comando para validar usuarios no /etc/tac_plus.conf
    check_users_tacplus = (f'if sudo cat /etc/tac_plus.conf | grep -w ' + username + ' > /dev/null; then echo "Found ' + username + '"; else echo "Not Found"; fi\n')
    # PUPPET
    # comando para validar usuarios no /etc/puppet/modules/usuarios-sec/manifests/init.pp
    check_users_puppet = (f'if sudo cat /etc/puppet/modules/usuarios-sec/manifests/init.pp | grep -w ' + username + ' > /dev/null; then echo "Found ' + username + '"; else echo "Not Found"; fi\n')
    # LDAP
    # comando para validar usuarios no ldap
    check_users_ldap = (f'if sudo ldapsearch -x -D "cn=gerente,c=BR"  -w P@ssw0rd -H ldap://192.168.248.170 -b "ou=Datacenter,o=Diveo,c=BR" -s sub uid="' + username + '" | grep "numEntries:" > /dev/null; then echo "Found "' + username + '; else echo "Not Found"; fi\n')
else:
    ### remover contas nas plataformas
    del_user = (f'sudo userdel -r ' + delusername + '\n')
    ### LDAP
    del_users_ldap = (f'ldapsearch -x -D "cn=gerente,c=BR"  -w P@ssw0rd -H ldap://192.168.248.170 -b "ou=Datacenter,o=Diveo,c=BR" -s sub uid="' + delusername + '" | grep dn > /tmp/user.ldif\n')
    create_ldif = (f'printf "\nchangetype: modrdn\nnewrdn: uid=' + delusername + '\ndeleteoldrdn: 1\nnewSuperior: ou=Desativados,o=Diveo,c=BR\n" >> /tmp/user.ldif\n')
    adjust_ldif = (f'sed '"/^\s*$/d"' /tmp/user.ldif > /tmp/user1.ldif\n')
    del_ldif = (f'rm -rf /tmp/user.ldif\n')
    mod_ldap_user = (f'ldapmodify -x -D "cn=gerente,c=BR" -w P@ssw0rd -H ldap://192.168.248.170 -f /tmp/user1.ldif\n')
    del_other_ldif = (f'rm -rf /tmp/user1.ldif\n')

    ### PUPPET
    puppet_01 = (f'sed -e /"' + delusername + '"/,+10 s/^/#/g -i /etc/puppet/modules/usuarios-sec/manifests/init.pp\n')
    puppet_02 = (f'sed -e ''s/"' + delusername + '",//g'' -i /etc/puppet/manifests/site.pp\n')
    puppet_03 = (f'sed -e ''s/"' + delusername + '"//g'' -i /etc/puppet/manifests/site.pp\n')
    puppet_04 = (f'sed -n ''/"' + delusername + '" {/,/}/p'' /etc/puppet/modules/usuarios-sec/manifests/init.pp\n')

    ### TACACs UOLHOST
    tacacs_sed_01 = (f'sed -e ''/"' + delusername + '"/,+4 s/^/#/g'' -i /etc/tac_plus.conf\n')
    tacacs_sed_02 = (f'sed -n ''/"' + delusername + '" {/,/}/p'' /etc/tac_plus.conf\n')
    restart_tacacs = (f'/etc/init.d/tac_plus restart\n')

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
        "ip": "192.168.2.131",
        "username": "sysadmin",
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
    if args.deluser == None:
        input_validation()
        for device in conteudo_json:
            if device["ip"] == "192.168.2.132":
                result = connect_jump(device, check_users_passwd)
            else:
                result = ssh_send_cmd(device, check_users_passwd)
                result = ssh_send_cmd(device, check_users_sudoers)
                result = ssh_send_cmd(device, check_users_sshd)
        print(f"\n{'#' * 50}\nFinished Executing Script\n{'#' * 50}")
        sys.exit()
    else:
        input_validation()
        for device in conteudo_json:
            if device["ip"] == "192.168.2.132":
                device_IP = device['ip']
                eventlog(device_IP, tasknumber)
                result = connect_jump(device, del_user)
            else:
                device_IP = device['ip']
                eventlog(device_IP, tasknumber)
                result = ssh_send_cmd(device, del_user)
        print(f"\n{'#' * 50}\nFinished Executing Script\n{'#' * 50}")
        sys.exit()

if __name__ == '__main__': main()