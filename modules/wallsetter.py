#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import sys
import json

import script
import db
from Wallpaper import Wallpaper
from Displays import Displays

def how_many_pictures_do_we_need(displays, differenciation_by):
    if differenciation_by == 'no':
        return 1
    if differenciation_by == 'display' or differenciation_by == 'monitor':
        return len(displays)
    if differenciation_by == 'space':
        return sum(len(display['Spaces']) for display in displays)

def main(origins, destination, store, retries, differenciation_by):
    displays = Displays.load()

    nb_files_to_load = how_many_pictures_do_we_need(displays, differenciation_by)
    files = []
    for i in xrange(0, nb_files_to_load):
        file = Wallpaper.download(origins, destination, store, retries)
        files.append(file)

    Wallpaper.eraseAll(destination, store)
    Wallpaper.set(displays, files, differenciation_by)
