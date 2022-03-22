#!/usr/bin/python
# coding: utf-8
import os
import subprocess

inputpath = '/home/sysadmin/Documents/ACLs/'
dirLog = '/tmp/'
listafiles = []


def dedupfiles(var):
    cmd = '/home/sysadmin/Documents/dedup.pl'
    # cmd = '/usr/bin/cat'
    file_name = (os.path.basename(var))
    file_name = (os.path.splitext(file_name)[0] + '.logs')
    filePath = os.path.join(dirLog, file_name)

    if os.path.exists(filePath):
        os.remove(filePath)
        # print("Deletado o log {}".format(file_name))
    else:
        print("Criado o log {}".format(file_name))
    outlog = open(filePath, "w")
    pipe = subprocess.Popen([cmd, var], stdout=outlog, stdin=subprocess.PIPE)
    # pipe.stdin.write(var)
    pipe.stdin.close()
    outlog.close()


for root, directories, files in os.walk(inputpath, topdown=True):
    for name in files:
        listafiles.append((os.path.join(root, name)))
        for i in range(len(listafiles)):
            a = str(listafiles[i])
            dedupfiles(a)
