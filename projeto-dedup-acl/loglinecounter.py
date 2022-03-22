#!/usr/bin/python
# coding: utf-8
import os

cmd = 'find /tmp/*.logs -type f -exec wc -l {} + | sort -rn'
os.system(cmd)
