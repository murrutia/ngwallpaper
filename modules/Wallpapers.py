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
import Database
import Script
from Displays import Displays

FILENAME = 'ngwallpaper'
EXTENSIONS = ['.jpg', '.jpeg', '.png']

class Wallpapers(object):

    def __init__(self, origins, destination, store, retries, differenciation_by):
        self.origins = origins
        self.destination = destination
        self.meta_folder = self.destination +'/_meta'
        self.store = store
        self.retries = retries
        self.differenciation_by = differenciation_by
        self.displays = Displays()

    def apply(self):
        files = []
        for i in xrange(0, self.pictures_needed_count()):
            file = self.download_new_wallpaper()
            files.append(file)

        self.eraseAll()
        self.set(files)

    def pictures_needed_count(self):
        if self.differenciation_by == 'no':
            return 1
        if self.differenciation_by == 'display' or self.differenciation_by == 'monitor':
            return self.displays.displayCount()
        if self.differenciation_by == 'space':
            return self.displays.spaceCount()

    def download_new_wallpaper(self):
        # Try to download a new wallpaper until all retries have been exhausted.
        for i in xrange(self.retries, 0, -1):
            # Initializations.
            file = None

            # Add some delay.
            time.sleep(min(float((self.retries - i) * 100), 5000.0) / 1000.0)

            # Ignore exceptions.
            try:
                # Fetch some random photo.
                wallpaper = Origins.ComposedOrigin(self.origins).photo

                assert \
                    wallpaper is not None, \
                    'Failed to fetch wallpaper'

                # Calculate destination filename.
                # Originally the filename changed only if we stored the picture, but we must now do it in no store
                # mode to be able to store multiple images in case of different pictures by displays / spaces.
                filename = self._filename(wallpaper['url'])

                # Skip if the file already exists.
                if not self.store or not self.exists(filename):
                    # Download selected photo.
                    file = self._download(wallpaper['url'], filename)
                    assert \
                        file is not None, \
                        'Failed to download wallpaper'

                    # Store meta data of the selected photo
                    if not os.path.exists(self.meta_folder):
                        os.makedirs(self.meta_folder)

                    with open(os.path.join(self.meta_folder, filename + '.txt'), 'w') as fd:
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
        if self.store and file is None:
            downloaded = []
            for extension in EXTENSIONS:
                downloaded.extend(glob.glob(destination + FILENAME + '-*' + extension))
            if len(downloaded) > 0:
                file = random.choice(downloaded)

        return file

    def exists(self, filename):
        for extension in EXTENSIONS:
            if len(glob.glob(self.destination + filename + extension)) > 0:
                return True
        return False

    def eraseFiles(self):
        for extension in EXTENSIONS:
            for f in glob.glob(self.destination + FILENAME + '*' + extension):
                print "suppression de "+ f
                os.remove(f)

    def eraseAll(self):
        Database.erase_db()
        if not self.store:
            Wallpaper.eraseFiles(self.destination)

    def  _filename(self, url):
        return FILENAME + '-' + hashlib.sha256(url).hexdigest()

    def _download(self, url, filename):
        # Initializations.
        file = None

        # Extract extension.
        extension = os.path.splitext(urlparse.urlparse(url).path)[1].lower()

        # Do not continue if the extension is not supported.
        if extension in EXTENSIONS:
            # Set destination file name.
            file = os.path.join(
                self.destination,
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

    def set(self, files):
        if self.differenciation_by == 'no':
            data_id = Database.insert_image(files[0])
            for display in self.displays:
                display_id = Database.insert_display(display['Display Identifier'])
                for space in display['Spaces']:
                    print 'display : '+ display['Display Identifier'] +' / space : '+ space['uuid']
                    space_id = Database.insert_space(space['uuid'])
                    Database.assign_image_to_space_display(space_id, display_id, data_id)

        if self.differenciation_by == 'display' or self.differenciation_by == 'monitor':
            for i in xrange(0, len(self.displays)):
                data_id = Database.insert_image(files[i])
                display = self.displays[i]
                display_id = Database.insert_display(display['Display Identifier'])
                for space in display['Spaces']:
                    space_id = Database.insert_space(space['uuid'])
                    Database.assign_image_to_space_display(space_id, display_id, data_id)

        if self.differenciation_by == 'space' :
            cpt_spaces = 0
            for i in xrange(0, len(self.displays)):
                display = self.displays[i]
                display_id = Database.insert_display(display['Display Identifier'])

                for space in display['Spaces']:
                    data_id = Database.insert_image(files[cpt_spaces])
                    space_id = Database.insert_space(space['uuid'])
                    Database.assign_image_to_space_display(space_id, display_id, data_id)

                    cpt_spaces += 1

        Script.shell('killall Dock')


