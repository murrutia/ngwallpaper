#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import sys

def shell(code, return_output=False):
    if return_output:
        func = subprocess.check_output
    else:
        func = subprocess.call
    return func(
        ['bash', '-c', code],
        shell=False,
        stdin=None,
        stderr=sys.stdout
    )

def sqlite(command, return_output=False):
    return shell(
        ''' sqlite3 ~/Library/Application\ Support/Dock/desktoppicture.db "%(command)s"
        ''' % { 'command': command },
        return_output
    )
