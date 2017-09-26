#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sys
import json

import script
import db
from Wallpaper import Wallpaper

def wallpapers_erase(destination, store):
    db.erase_db()
    if not store:
        Wallpaper.eraseAll(destination)

def load_displays():
    spaces_display_configuration = json.loads(script.shell('plutil -convert json ~/Library/Preferences/com.apple.spaces.plist -o -', return_output=True))
    displays = spaces_display_configuration["SpacesDisplayConfiguration"]["Management Data"]["Monitors"]
    displays = filterout_virtual_display(displays)
    determine_main_display_uuid(displays)
    return displays

def filterout_virtual_display(displays):
    return filter(lambda m: "Collapsed Space" not in m, displays)

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

def how_many_pictures_do_we_need(displays, differenciation_by):
    if differenciation_by == 'no':
        return 1
    if differenciation_by == 'display' or differenciation_by == 'monitor':
        return len(displays)
    if differenciation_by == 'space':
        return sum(len(display['Spaces']) for display in displays)

def wallpapers_set(displays, files, differenciation_by):
    if differenciation_by == 'no':
        data_id = db.insert_image(files[0])
        for display in displays:
            display_id = db.insert_display(display['Display Identifier'])
            for space in display['Spaces']:
                print 'display : '+ display['Display Identifier'] +' / space : '+ space['uuid']
                space_id = db.insert_space(space['uuid'])
                db.assign_image_to_space_display(space_id, display_id, data_id)

    if differenciation_by == 'display' or differenciation_by == 'monitor':
        for i in xrange(0, len(displays)):
            data_id = db.insert_image(files[i])
            display = displays[i]
            display_id = db.insert_display(display['Display Identifier'])
            for space in display['Spaces']:
                space_id = db.insert_space(space['uuid'])
                db.assign_image_to_space_display(space_id, display_id, data_id)

    if differenciation_by == 'space' :
        cpt_spaces = 0
        for i in xrange(0, len(displays)):
            display = displays[i]
            display_id = db.insert_display(display['Display Identifier'])

            for space in display['Spaces']:
                data_id = db.insert_image(files[cpt_spaces])
                space_id = db.insert_space(space['uuid'])
                db.assign_image_to_space_display(space_id, display_id, data_id)

                cpt_spaces += 1

    script.shell('killall Dock')

def main(origins, destination, store, retries, differenciation_by):
    displays = load_displays()

    nb_files_to_load = how_many_pictures_do_we_need(displays, differenciation_by)
    files = []
    for i in xrange(0, nb_files_to_load):
        file = Wallpaper.download(origins, destination, store, retries)
        files.append(file)

    wallpapers_erase(destination, store)
    wallpapers_set(displays, files, differenciation_by)
