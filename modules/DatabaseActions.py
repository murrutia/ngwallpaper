#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Script

class DatabaseActions(object):

    def __init__(self, database=None):
        self.database = database or '~/Library/Application\ Support/Dock/desktoppicture.db'

    def sqlite(self, command, return_output=False):
        return Script.shell(
            ''' sqlite3 %(database)s "%(command)s"
            ''' % {
                'database': self.database,
                'command': command.replace('"','\\"')
            },
            return_output
        )


    def insert_image(self, file):
        return self.sqlite(
            '''insert into data (value) values ('%(file)s'); select last_insert_rowid()
            ''' % { 'file' : file },
            return_output=True)

    def insert_display(self, display_uuid):
        return self.sqlite(
            '''insert into displays (display_uuid) values ('%(uuid)s'); select last_insert_rowid()
            ''' % { 'uuid': display_uuid },
            return_output=True)

    def insert_space(self, space_uuid):
        return self.sqlite(
            '''insert into spaces (space_uuid) values ('%(uuid)s'); select last_insert_rowid()
            ''' % { 'uuid': space_uuid },
            return_output=True)

    def assign_image_to_space_display(self, space_id, display_id, data_id):
        picture_id = self.sqlite(
            '''insert into pictures (space_id, display_id) values (%(space_id)s, %(display_id)s); select last_insert_rowid()
            ''' % { 'space_id': space_id, 'display_id': display_id },
            return_output=True)
        return self.sqlite(
            '''insert into preferences (key, data_id, picture_id) values (1, %(data_id)s, %(picture_id)s); select last_insert_rowid()
            ''' % { 'data_id': data_id, 'picture_id': picture_id },
            return_output=True)

    def get_display_uuids(self):
        rows = self.sqlite(
                'select rowid, display_uuid from displays',
                return_output=True).split('\n')
        displays = self._weed_out_empty_and_duplicate_displays(rows)
        return displays

    def _weed_out_empty_and_duplicate_displays(self, rows):
        displays = []
        to_discard = []
        for row in rows:
            if row:
                rowid, uuid = row.split('|')
                if uuid == '' or uuid in displays:
                    to_discard.append(rowid)
                else:
                    displays.append(uuid)
        if to_discard:
            for rowid in to_discard:
                self.sqlite('''delete from displays where rowid=%(rowid)s ''' % { 'rowid': rowid })
        return displays

    def erase_db(self):
        self.sqlite('delete from pictures where 1')
        self.sqlite('delete from displays where 1')
        self.sqlite('delete from spaces where 1')
        self.sqlite('delete from data where 1')
