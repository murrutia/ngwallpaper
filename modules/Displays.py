#!/usr/bin/env python
# utf-8

import json

import Script
import Database

class Displays(object):

    def __init__(self):
        spaces_display_configuration = json.loads(Script.shell('plutil -convert json ~/Library/Preferences/com.apple.spaces.plist -o -', return_output=True))
        self.displays = spaces_display_configuration["SpacesDisplayConfiguration"]["Management Data"]["Monitors"]
        self.filterout_virtual_display()
        self.determine_main_display_uuid()

    def filterout_virtual_display(self):
        self.displays = filter(lambda m: "Collapsed Space" not in m, self.displays)

    def determine_main_display_uuid(self):
        # In the plist we've loaded earlier, on a MBP the Main Display's UUID isn't listed
        # so before we alter the wallpaper database, we retrieve it by getting them all
        # and removing those we know. By elimination, the last one should be the main.
        uuids = Database.get_display_uuids()
        main_display = None
        for display in self.displays:
            uuid = display["Display Identifier"]
            if uuid == 'Main':
                main_display = display
            elif uuid in uuids:
                uuids.remove(display["Display Identifier"])
        if len(uuids) == 1 and main_display != None:
            main_display["Display Identifier"] = uuids[0]
        else:
            sys.stderr.write('Error in determining main display uuid !\n')
            sys.exit(1)

    def __getitem__(self, item):
        return self.displays[item]

    def __len__(self):
        return len(self.displays)

    def displayCount(self):
        return len(self.displays)

    def spaceCount(self):
        return sum(len(display['Spaces']) for display in self.displays)
