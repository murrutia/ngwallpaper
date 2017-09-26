#!/usr/bin/env python
# utf-8

import json

import script
import db

class Displays(object):

    @staticmethod
    def load():
        spaces_display_configuration = json.loads(script.shell('plutil -convert json ~/Library/Preferences/com.apple.spaces.plist -o -', return_output=True))
        displays = spaces_display_configuration["SpacesDisplayConfiguration"]["Management Data"]["Monitors"]
        displays = Displays.filterout_virtual_display(displays)
        Displays.determine_main_display_uuid(displays)
        return displays

    @staticmethod
    def filterout_virtual_display(displays):
        return filter(lambda m: "Collapsed Space" not in m, displays)

    @staticmethod
    def determine_main_display_uuid(displays):
        # In the plist we've loaded earlier, on a MBP the Main Display's UUID isn't listed
        # so before we alter the wallpaper database, we retrieve it by getting them all
        # and removing those we know. By elimination, the last one should be the main.
        uuids = db.get_display_uuids()
        main_display = None
        for display in displays:
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
