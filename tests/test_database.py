#!/usr/bin/env python
# coding: utf-8

import os
import pytest

import Script
from DatabaseActions import DatabaseActions

# test database object
db_path = "/tmp/desktoppictures.db"
DB = DatabaseActions(db_path)


@pytest.yield_fixture
def empty_database():
    here = os.path.dirname(__file__)
    with open(os.path.join(here, '_database-schema.sql'), 'r') as f:
        schema = f.read()
    DB.sqlite(schema)
    yield None
    Script.shell('rm '+db_path)

display_1_uuid = "C1DBC4DB-E6CC-47AE-ABB0-E2F46F470BAA"
display_2_uuid = "C2DC826E-5AD8-4D2F-8E67-6658432D80A7"
@pytest.fixture
def database_with_displays(empty_database):
    query = '''insert into displays (display_uuid) values ("%(uuid1)s"), ("%(uuid2)s")
            ''' % {
                'uuid1': display_1_uuid,
                'uuid2': display_2_uuid
            }
    DB.sqlite(query, True)

def test_wallpapers_database_exists():
    # if it exists, there should be at least one row in the table sqlite_master
    query = 'select * from sqlite_master limit 0,1'
    line = DatabaseActions().sqlite(query, True).strip()
    assert line != ""

def test_create_database(empty_database):
    query = 'select * from sqlite_master limit 0,1'
    line = DB.sqlite(query, return_output=True).strip()
    assert line != ""

def test_see_all_displays_in_database(database_with_displays):
    displays = DB.get_display_uuids()
    assert displays[0] == display_1_uuid
    assert displays[1] == display_2_uuid

def test_see_all_displays_with_extra_empty_row(database_with_displays):
    DB.sqlite('insert into displays (display_uuid) values ("")')
    displays = DB.get_display_uuids()
    assert len(displays) == 2
    assert display_1_uuid in displays
    assert display_2_uuid in displays

def test_see_all_displays_with_duplicate_row(database_with_displays):
    DB.sqlite('insert into displays (display_uuid) values ("%(uuid)s")' % { 'uuid': display_1_uuid })
    displays = DB.get_display_uuids()
    assert len(displays) == 2
    assert display_1_uuid in displays
    assert display_2_uuid in displays

