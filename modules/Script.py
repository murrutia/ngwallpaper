#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys
import json
import subprocess

def shell(code, return_output=False):
    if return_output:
        func = shell_and_output
    else:
        func = subprocess.call
    return func(
        ['bash', '-c', code],
        shell=False,
        stdin=None,
        stderr=sys.stdout
    )

def shell_and_output(*args, **kwargs):
    output = subprocess.check_output(*args, **kwargs)
    return output[:-1] if output[-1:] == '\n' else output # remove the last new line character

def load_json_file(file):
    json_str = shell('''plutil -convert json %(file)s -o -''' % { 'file': file },
                 return_output=True)
    return json.loads(json_str)

class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_error(text, color=bcolors.FAIL):
    sys.stderr.write(color + text + bcolors.ENDC)
