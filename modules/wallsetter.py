#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sys
import os
import urlparse
import subprocess
import urllib2
import json
import hashlib
import glob

import wrappers as wp
import script
import db

FILENAME = 'ngwallpaper'
EXTENSIONS = ['.jpg', '.jpeg', '.png']


def wallpaper_exists(destination, filename):
    for extension in EXTENSIONS:
        if len(glob.glob(destination + filename + extension)) > 0:
            return True
    return False

def wallpapers_erase(destination, store):
    db.erase_db()
    if not store:
        for extension in EXTENSIONS:
            for f in glob.glob(destination + FILENAME + '*' + extension):
                print "suppression de "+ f
                os.remove(f)

def download_wallpaper(url, destination, filename):
    # Initializations.
    file = None

    # Extract extension.
    extension = os.path.splitext(urlparse.urlparse(url).path)[1].lower()

    # Do not continue if the extension is not supported.
    if extension in EXTENSIONS:
        # Set destination file name.
        file = os.path.join(
            destination,
            filename + extension)

        # Download URL.
        ifp = urllib2.urlopen(url, None, wp.HTTP_TIMEOUT)
        assert \
            ifp.getcode() == 200, \
            'Got unexpected HTTP response'
        with open(file, 'wb') as ofd:
            ofd.write(ifp.read())
        ifp.close()

    # Done!
    return file

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


def  generate_filename(url):
    return FILENAME + '-' + hashlib.sha256(url).hexdigest()

def download_picture(origins, destination, store, retries):
    # Try to download a new wallpaper until all retries have been exhausted.
    for i in xrange(retries, 0, -1):
        # Initializations.
        file = None

        # Add some delay.
        time.sleep(min(float((retries - i) * 100), 5000.0) / 1000.0)

        # Ignore exceptions.
        try:
            # Fetch some random photo.
            wallpaper = wp.ComposedOrigin(origins).photo

            assert \
                wallpaper is not None, \
                'Failed to fetch wallpaper'

            # Calculate destination filename.
            # Originally the filename changed only if we stored the picture, but we must now do it in no store
            # mode to be able to store multiple images in case of different pictures by displays / spaces.
            filename = generate_filename(wallpaper['url'])

            # Skip if the file already exists.
            if not store or not wallpaper_exists(destination, filename):
                # Download selected photo.
                file = download_wallpaper(wallpaper['url'], destination, filename)
                assert \
                    file is not None, \
                    'Failed to download wallpaper'

                # Store meta data of the selected photo
                meta_folder = destination +'/_meta'
                if not os.path.exists(meta_folder):
                    os.makedirs(meta_folder)

                with open(os.path.join(meta_folder, filename + '.txt'), 'w') as fd:
                    fd.write(wallpaper['index'] + '\n')
                    fd.write(wallpaper['url'] + '\n')

                # Done!
                break
            else:
                sys.stdout.write('%(attempt)d: %(message)s\n' % {
                    'attempt': i,
                    'message': 'wallpaper already exists (%s)' % wallpaper['url'],
                })
        except Exception as e:
            sys.stdout.write('%(attempt)d: %(message)s\n' % {
                'attempt': i,
                'message': 'unexpected failure (%s)' % e,
            })

    # If a new wallpaper was not downloaded, try to use an existing one.
    if store and file is None:
        downloaded = []
        for extension in EXTENSIONS:
            downloaded.extend(glob.glob(destination + FILENAME + '-*' + extension))
        if len(downloaded) > 0:
            file = random.choice(downloaded)

    return file

def wallpapers_set(displays, files, differenciation_by):
    if differenciation_by == 'no':
        data_id = db.insert_image(files[0])
        for display in displays:
            display_id = db.insert_display(display['Display Identifier'])
            for space in display['Spaces']:
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
        file = download_picture(origins, destination, store, retries)
        files.append(file)

    wallpapers_erase(destination, store)
    wallpapers_set(displays, files, differenciation_by)
