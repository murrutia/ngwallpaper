#!/usr/bin/env python
# utf-8

import os
import pytest

import Script
import Database as DB

# test database path
db_path="/tmp/desktoppictures.db"

@pytest.yield_fixture
def empty_database():
    here = os.path.dirname(__file__)
    with open(os.path.join(here, '_database-schema.sql'), 'r') as f:
        schema = f.read()
    Script.sqlite(schema, database=db_path)
    yield None
    Script.shell('rm '+db_path)

def test_wallpapers_database_exists():
    # if it exists, there should be at least one row in the table sqlite_master
    query = 'select * from sqlite_master limit 0,1'
    line = Script.sqlite(query, return_output=True).strip()
    assert line != ""

def test_create_database(empty_database):
    print "test has run"
