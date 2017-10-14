#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import json

import Script
from DatabaseActions import DatabaseActions

class Displays(object):

    def __init__(self):
        self.db = DatabaseActions()
        spaces_display_configuration = Script.load_json_file("~/Library/Preferences/com.apple.spaces.plist")
        self.displays = spaces_display_configuration["SpacesDisplayConfiguration"]["Management Data"]["Monitors"]
        self.filterout_virtual_display()
        self.determine_main_display_uuid()

    def filterout_virtual_display(self):
        self.displays = filter(lambda m: "Current Space" in m, self.displays)

    def determine_main_display_uuid(self, retry=False):
        # In the plist we've loaded earlier, on a MBP the Main Display's UUID isn't listed
        # so before we alter the wallpaper database, we retrieve it by getting them all
        # and removing those we know. By elimination, the last one should be the main.
        uuids = self.db.get_display_uuids()
        main_display = None
        for display in self.displays:
            uuid = display["Display Identifier"]
            if uuid == 'Main':
                main_display = display
            elif uuid in uuids:
                uuids.remove(display["Display Identifier"])
        if len(uuids) == 1 and main_display != None:
            main_display["Display Identifier"] = uuids[0]
        elif not retry:
            self._try_refreshing_wallpaper_database()
            self.determine_main_display_uuid(True)
        else:
            Script.print_error('''Error while determining main display uuid !
Try resetting manually a desktop backgoung and relaunching this command
''')
            sys.exit(1)

    def _try_refreshing_wallpaper_database(self):
        self.db.sqlite('delete from displays where 1')
        Script.shell('''osascript -e 'tell application "Finder" to set desktop picture to POSIX file "/Library/Desktop Pictures/Snow.jpg"' ''')

    def __getitem__(self, item):
        return self.displays[item]

    def __len__(self):
        return len(self.displays)

    def displayCount(self):
        return len(self.displays)

    def spaceCount(self):
        return sum(len(display['Spaces']) for display in self.displays)
