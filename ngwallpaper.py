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

import argparse
import tempfile
from modules import wallsetter as ws
from modules import wrappers as wp

if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '--use-ngm-latest', dest='origins', required=False,
        action='append_const', const=wp.NGMLatest(),
        help='enable "NGM latest" repository')

    parser.add_argument(
        '--use-ngm-archive', dest='origins', required=False,
        action='append_const', const=wp.NGMArchive(),
        help='enable "NGM archive" repository')

    parser.add_argument(
        '--use-miscellaneous-galleries', dest='origins', required=False,
        action='append_const', const=wp.MiscellaneousGalleriesOrigin(wp.MISCELANEOUS_GALLERIES),
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

    if options.origins and options.retries > 0:
        ws.main(options.origins, options.destination, options.store, options.retries, options.differenciation_by)
    else:
        parser.print_help()
        sys.exit(1)

