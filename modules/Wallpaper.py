#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import glob
import time
import hashlib
import urllib2
import urlparse

import Origins
import db
import script

FILENAME = 'ngwallpaper'
EXTENSIONS = ['.jpg', '.jpeg', '.png']

class Wallpaper(object):

    @staticmethod
    def download(origins, destination, store, retries):
        # Try to download a new wallpaper until all retries have been exhausted.
        for i in xrange(retries, 0, -1):
            # Initializations.
            file = None

            # Add some delay.
            time.sleep(min(float((retries - i) * 100), 5000.0) / 1000.0)

            # Ignore exceptions.
            try:
                # Fetch some random photo.
                wallpaper = Origins.ComposedOrigin(origins).photo

                assert \
                    wallpaper is not None, \
                    'Failed to fetch wallpaper'

                # Calculate destination filename.
                # Originally the filename changed only if we stored the picture, but we must now do it in no store
                # mode to be able to store multiple images in case of different pictures by displays / spaces.
                filename = Wallpaper._filename(wallpaper['url'])

                # Skip if the file already exists.
                if not store or not Wallpaper.exists(destination, filename):
                    # Download selected photo.
                    file = Wallpaper._download(wallpaper['url'], destination, filename)
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

    @staticmethod
    def exists(destination, filename):
        for extension in EXTENSIONS:
            if len(glob.glob(destination + filename + extension)) > 0:
                return True
        return False

    @staticmethod
    def eraseFiles(destination):
        for extension in EXTENSIONS:
            for f in glob.glob(destination + FILENAME + '*' + extension):
                print "suppression de "+ f
                os.remove(f)

    @staticmethod
    def eraseAll(destination, store):
        db.erase_db()
        if not store:
            Wallpaper.eraseFiles(destination)

    @staticmethod
    def  _filename(url):
        return FILENAME + '-' + hashlib.sha256(url).hexdigest()

    @staticmethod
    def _download(url, destination, filename):
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
            ifp = urllib2.urlopen(url, None, Origins.HTTP_TIMEOUT)
            assert \
                ifp.getcode() == 200, \
                'Got unexpected HTTP response'
            with open(file, 'wb') as ofd:
                ofd.write(ifp.read())
            ifp.close()

        # Done!
        return file

    @staticmethod
    def set(displays, files, differenciation_by):
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


