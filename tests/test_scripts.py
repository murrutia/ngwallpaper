#!/usr/bin/env python
# utf-8

import Script

def test_script_returns_code():
    assert Script.shell('true') == 0
    assert Script.shell('false') == 1

def test_script_returns_output():
    output = Script.shell('echo yes', return_output=True).strip()
    assert output == 'yes'
