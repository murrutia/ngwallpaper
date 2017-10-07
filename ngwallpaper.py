#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
National Geographic Wallpaper
=============================

Please, check out https://github.com/carlosabalde/ngwallpaper
for a detailed description and other useful information.

:copyright: (c) 2014 by Carlos Abalde <carlos.abalde@gmail.com>.
:license: BSD, see LICENSE for more details.
'''

import os
import sys
import json
import argparse
import tempfile

from time import time, gmtime, strftime

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules'))

import Origins
from KnownOrigins import *
from Wallpapers import Wallpapers

if __name__ == '__main__':

    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--use-reddit-sub', dest='reddit_sub_origins', required=False,
        action='append',
        help='enable "Reddit Sub" repository')

    parser.add_argument(
        '--use-reddit-user', dest='reddit_user_origins', required=False,
        action='append',
        help='enable "Reddit User" repository')

    parser.add_argument(
        '--use-ngm-latest', dest='origins', required=False,
        action='append_const', const=Origins.NGMLatest(),
        help='enable "NGM latest" repository')

    parser.add_argument(
        '--use-ngm-archive', dest='origins', required=False,
        action='append_const', const=Origins.NGMArchive(),
        help='enable "NGM archive" repository')

    parser.add_argument(
        '--use-ngm-galleries', dest='galleries_ngm', required=False,
        action='store_true',
        help='enable "Miscellaneous galleries" repository')

    parser.add_argument(
        '--use-reddit-galleries', dest='galleries_reddit', required=False,
        action='store_true',
        help='enable "Reddit galleries" repository')

    parser.add_argument(
        '--destination', dest='destination', type=str, required=False,
        default=tempfile.gettempdir(),
        help='set location of downloaded wallpapers')

    parser.add_argument(
        '--store', dest='store', required=False,
        action='store_true',
        help='if enabled previously downloaded wallpapers are not removed')

    parser.add_argument(
        '--store-all', dest='store_all', required=False,
        action='store_true',
        help='if enabled all wallpapers in repositories will be stored locally')

    parser.add_argument(
        '--retries', dest='retries', type=int, required=False,
        default=1,
        help='number of retries before failing / using a previously downloaded wallpaper')

    parser.add_argument(
        '--differenciation-by', dest='differenciation_by', required=False,
        default='no',
        help='Differenciation of images by display or space (possible values : no (default), display, space)')

    parser.add_argument(
        '--load-from-storage', dest='load_from_storage', required=False,
        action='store_true',
        help='if enabled no wallpaper will be downloaded, it will be chosen from those already in store')

    parser.add_argument(
        '--minimum-size', dest='minimum_size', type=str, required=False,
        default='0x0',
        help='the minimum size for the images to be downloaded, in the format WIDTHxHEIGHT (default : 0x0)')

    parser.add_argument(
        '--clear-cache', dest='clear_cache', required=False,
        action="store_true",
        help='force redownload of html pages of the wallpaper repositories')

    options = parser.parse_args()

    if not options.origins:
        options.origins = []

    if options.reddit_sub_origins:
        for sub in options.reddit_sub_origins:
            options.origins.append(Origins.RedditSubOrigin(sub))

    if options.reddit_user_origins:
        for user in options.reddit_user_origins:
            options.origins.append(Origins.RedditUserOrigin(user))

    if options.galleries_ngm:
        options.origins.append(Origins.ComposedOrigin().addOriginDefinitions(Galleries['NGM']))

    if options.galleries_reddit:
        options.origins.append(Origins.ComposedOrigin().addOriginDefinitions(Galleries['Reddit']))

    start = time()
    print "start time : "+ strftime("%Y-%m-%d %H:%M:%S", gmtime())

    if options.origins and (options.retries > 0 or options.load_from_storage):
        wallpapers = Wallpapers(options)
        if options.store_all:
            wallpapers.store_all()
        wallpapers.apply()

        end = time()
        print "execution time : "+ str(end - start) +"s\n"
    else:
        parser.print_help()
        sys.exit(1)

