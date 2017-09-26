#!/usr/bin/env python
# -*- coding: utf-8 -*-

import script

def insert_image(file):
    return script.sqlite(
        '''insert into data (value) values ('%(file)s'); select last_insert_rowid()
        ''' % { 'file' : file },
        return_output=True
    )

def insert_display(display_uuid):
    return script.sqlite(
        '''insert into displays (display_uuid) values ('%(uuid)s'); select last_insert_rowid()
        ''' % { 'uuid': display_uuid },
        return_output=True
    )

def insert_space(space_uuid):
    return script.sqlite(
        '''insert into spaces (space_uuid) values ('%(uuid)s'); select last_insert_rowid()
        ''' % { 'uuid': space_uuid },
        return_output=True
    )

def assign_image_to_space_display(space_id, display_id, data_id):
    picture_id = script.sqlite(
        '''insert into pictures (space_id, display_id) values (%(space_id)s, %(display_id)s); select last_insert_rowid()
        ''' % { 'space_id': space_id, 'display_id': display_id },
        return_output=True
    )
    return script.sqlite(
        '''insert into preferences (key, data_id, picture_id) values (1, %(data_id)s, %(picture_id)s); select last_insert_rowid()
        ''' % { 'data_id': data_id, 'picture_id': picture_id },
        return_output=True
    )


def get_display_uuids():
    return script.sqlite(
        'select display_uuid from displays',
        return_output=True
    ).strip()\
    .split('\n')

def erase_db():
    # delete all associations and data in DB through actions triggered py picture deletions
    script.sqlite('delete from pictures where 1')
