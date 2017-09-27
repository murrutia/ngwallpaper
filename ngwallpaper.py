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

import sys
import json
import time
import argparse
import tempfile

sys.path.append('modules')
import Origins
import KnownOrigins
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
        '--use-miscellaneous-galleries', dest='origins', required=False,
        action='append_const', const=Origins.ComposedOrigin().addOriginDefinitions(KnownOrigins.NGMGalleries),
        help='enable "Miscellaneous galleries" repository')

    parser.add_argument(
        '--destination', dest='destination', type=str, required=False,
        default=tempfile.gettempdir(),
        help='set location of downloaded wallpapers')

    parser.add_argument(
        '--store', dest='store', required=False,
        action='store_true',
        help='if enabled previously downloaded wallpapers are not removed')

    parser.add_argument(
        '--retries', dest='retries', type=int, required=False,
        default=100,
        help='number of retries before failing / using a previously downloaded wallpaper')

    parser.add_argument(
        '--differenciation_by', dest='differenciation_by', required=False,
        default='no',
        help='Differenciation of images by display or space (possible values : no (default), display, space)')

    options = parser.parse_args()

    if not options.origins:
        options.origins = []

    if options.reddit_sub_origins:
        for sub in options.reddit_sub_origins:
            options.origins.append(Origins.RedditSubOrigin(sub))

    if options.reddit_user_origins:
        for user in options.reddit_user_origins:
            options.origins.append(Origins.RedditUserOrigin(user))

    if options.origins and options.retries > 0:
        Wallpapers(options.origins, options.destination, options.store, options.retries, options.differenciation_by)\
            .apply()
    else:
        parser.print_help()
        sys.exit(1)

