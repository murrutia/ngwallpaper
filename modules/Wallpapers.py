#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import glob
import json
import time
import random
import hashlib
import urllib2
import urlparse

import Script
import Origins
import getimageinfo
from Displays import Displays
from DatabaseActions import DatabaseActions

class Wallpapers(object):

    def __init__(self, options):
        self.origins = Origins.ComposedOrigin(options.origins)
        self.destination = options.destination
        self.meta_folder = self.destination +'/_meta'
        self.store = options.store
        self.retries = options.retries
        self.differenciation_by = options.differenciation_by
        self.load_from_storage = options.load_from_storage
        self.minimum_size = [ int(x) for x in options.minimum_size.split('x') ]
        self.displays = Displays()
        self.db = DatabaseActions()

        if options.clear_cache:
            self.origins.clear_cache()

    def apply(self):
        self.eraseAll()

        files = []
        for i in xrange(0, self.pictures_needed_count()):
            file = self.download_wallpaper()
            files.append(file)

        self.set(files)

    def pictures_needed_count(self):
        if self.differenciation_by == 'no':
            return 1
        if self.differenciation_by == 'display' or self.differenciation_by == 'monitor':
            return self.displays.displayCount()
        if self.differenciation_by == 'space':
            return self.displays.spaceCount()

    def store_all(self):
        # if we store all the images, we consider that we are in storage mode,
        # so we set `store` to True to avoid erasing them all in the final step
        self.store = True

        wallpapers = self.origins.photos

        for wallpaper in wallpapers:
            self.download_wallpaper(wallpaper)

    def download_wallpaper(self, wallpaper=None):

        randomize = True if wallpaper is None else False

        if not self.load_from_storage:
            # Try to download a new wallpaper until all retries have been exhausted.
            for i in xrange(self.retries, 0, -1):
                # Initializations.
                file = None

                # Ignore exceptions.
                try:
                    if randomize:
                        wallpaper = self.origins.photo
                    assert wallpaper is not None, "Failed to get wallpaper info. randomize : ["+ str(randomize) +"]"
                    file = self._download_or_retrieve(wallpaper)

                    break

                except Exception as e:
                    sys.stdout.write('%(attempt)d: %(message)s\n' % {
                        'attempt': i,
                        'message': 'unexpected failure (%s)' % e,
                    })
                    # Add a delay before next retry
                    if i > 0 and wallpaper:
                        time.sleep(wallpaper.origin.download_delay)

        if not file and randomize:
            file = self._get_a_wallpaper_already_stored()

        return file

    def _download_or_retrieve(self, wallpaper):
        file = None
        wallpaper.destination = self.destination
        # Do not continue if the extension is not supported.
        if wallpaper.extension in Origins.EXTENSIONS:
            file = wallpaper.filepath
            if os.path.isfile(file):
                print "already downloaded : "+ wallpaper.url
            else:
                file = self._download(wallpaper)
                assert file is not None, 'Failed to download wallpaper : ' + str(wallpaper)

        return file

    def _download(self, wallpaper):
        file = wallpaper.filepath

        print "downloading : "+ wallpaper.url
        # Download URL. The User-Agent header is set to avoid 403 errors from some websites
        headers = { 'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36' }
        request = urllib2.Request(wallpaper.url, headers=headers)
        ifp = urllib2.urlopen(request)
        assert ifp.getcode() == 200, 'Got unexpected HTTP response'
        wallpaper.image_type, wallpaper.width, wallpaper.height = getimageinfo.getImageInfo(ifp)
        ifp.close()

        if not wallpaper.respects_dimensions(self.minimum_size):
            print "Image size of "+ str(wallpaper.width) +'x'+ str(wallpaper.height) +' : will not be downloaded because smaller than '+ 'x'.join([ str(x) for x in self.minimum_size ])
        else:
            ifp = urllib2.urlopen(request)

            with open(file, 'wb') as ofd:
                ofd.write(ifp.read())
            self._store_wallpaper_metadata(wallpaper)
            ifp.close()


        # Done!
        return file

    def _store_wallpaper_metadata(self, wallpaper):
        # Store meta data of the selected photo
        if not os.path.exists(self.meta_folder):
            os.makedirs(self.meta_folder)
        with open(os.path.join(self.meta_folder, wallpaper.filename + '.txt'), 'w') as fd:
            fd.write(str(wallpaper))

    def _get_a_wallpaper_already_stored(self):
        file = None
        filename_bases = self.origins.filename_base
        downloaded = []
        for filename_base in filename_bases:
            downloaded.extend(glob.glob(self.destination + filename_base +'*'))
        if len(downloaded) > 0:
            file = random.choice(downloaded)

        if file:
            print 'retrieving from storage : '+ file
        return file

    def eraseFiles(self):
        for f in glob.glob(os.path.join(self.destination, Origins.FILENAMEBASE + '*')):
            print "suppression de "+ f
            os.remove(f)

    def eraseAll(self):
        self.db.erase_db()
        if not self.store:
            self.eraseFiles()


    def set(self, files):
        if self.differenciation_by == 'no':
            data_id = self.db.insert_image(files[0])
            for display in self.displays:
                display_id = self.db.insert_display(display['Display Identifier'])
                for space in display['Spaces']:
                    space_id = self.db.insert_space(space['uuid'])
                    self.db.assign_image_to_space_display(space_id, display_id, data_id)

        if self.differenciation_by == 'display' or self.differenciation_by == 'monitor':
            for i in xrange(0, len(self.displays)):
                data_id = self.db.insert_image(files[i])
                display = self.displays[i]
                display_id = self.db.insert_display(display['Display Identifier'])
                for space in display['Spaces']:
                    space_id = self.db.insert_space(space['uuid'])
                    self.db.assign_image_to_space_display(space_id, display_id, data_id)

        if self.differenciation_by == 'space' :
            cpt_spaces = 0
            for i in xrange(0, len(self.displays)):
                display = self.displays[i]
                display_id = self.db.insert_display(display['Display Identifier'])

                for space in display['Spaces']:
                    data_id = self.db.insert_image(files[cpt_spaces])
                    space_id = self.db.insert_space(space['uuid'])
                    self.db.assign_image_to_space_display(space_id, display_id, data_id)

                    cpt_spaces += 1

        Script.shell('killall Dock')
