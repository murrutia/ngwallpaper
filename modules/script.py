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

def sqlite(command, return_output=False, database='~/Library/Application\ Support/Dock/desktoppicture.db'):
    return shell(
        ''' sqlite3 %(database)s "%(command)s"
        ''' % { 'database': database, 'command': command },
        return_output
    )
