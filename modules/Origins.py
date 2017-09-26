#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import urllib2
import re
import abc
import random
import urlparse
from xml.etree import ElementTree
from BeautifulSoup import BeautifulSoup
import json

HTTP_TIMEOUT = 30

MISCELANEOUS_GALLERIES = [
    # Life in Color.
    'http://photography.nationalgeographic.com/photography/photos/life-color-kaleidoscope/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-red/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-orange/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-yellow/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-green/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-blue/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-purple/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-gold/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-silver/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-white/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-brown/',
    'http://photography.nationalgeographic.com/photography/photos/life-color-black/',
    # Patterns in Nature.
    'http://photography.nationalgeographic.com/photography/photos/patterns-flora/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-nature-reflections/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-landscapes/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-nature-trees/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-animals/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-butterflies/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-nature-rainbows/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-island-aerials/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-snow-ice/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-rocks-lava/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-water/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-coral/',
    'http://photography.nationalgeographic.com/photography/photos/patterns-aurorae/',
    # Other.
    'http://photography.nationalgeographic.com/photography/photos/visions-of-earth-wallpapers',
    'http://animals.nationalgeographic.com/animals/photos/bird-wallpapers/',
    'http://photography.nationalgeographic.com/photography/photos/underwater-wrecks/',
    'http://photography.nationalgeographic.com/photography/photos/mysterious-earth/',
    'http://photography.nationalgeographic.com/photography/photos/ocean-soul/',
    'http://photography.nationalgeographic.com/photography/photos/extreme-earth/',
    'http://photography.nationalgeographic.com/photography/photos/megatransect-gallery/',
    'http://photography.nationalgeographic.com/photography/photos/cave-exploration/',
    'http://photography.nationalgeographic.com/photography/photos/volcano-exploration/',
    'http://photography.nationalgeographic.com/photography/photos/north-pole-expeditions/',
    'http://adventure.nationalgeographic.com/adventure/everest/climbing-everest-photo-gallery/',
    'http://adventure.nationalgeographic.com/adventure/mount-everest-photo-gallery',
]

class Origin(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractproperty
    def photo(self):
        pass


class LeafOrigin(Origin):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(LeafOrigin, self).__init__()

    @property
    def _timeout(self):
        return HTTP_TIMEOUT

    def _expand_href(self, url, href):
        if href.startswith('http://') or href.startswith('https://'):
            return href
        elif href.startswith('//'):
            return 'http:' + href
        else:
            parsed = urlparse.urlparse(url)
            return parsed.scheme + '://' + parsed.netloc + href


class NGMOrigin(LeafOrigin):
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        super(NGMOrigin, self).__init__()
        self._cache = []

    @property
    def photo(self):
        result = None
        if self._indices:
            index = random.choice(self._indices)
            fp = urllib2.urlopen(index, None, self._timeout)
            if fp.getcode() == 200:
                urls = self._parse_photo_urls(fp.read())
                if urls:
                    result = {
                        'index': index,
                        'url': random.choice(urls),
                    }
            fp.close()
        return result

    @property
    def _indices(self):
        if not self._cache:
            fp = urllib2.urlopen(self._root_url + self._path, None, self._timeout)
            if fp.getcode() == 200:
                options = BeautifulSoup(fp.read()).\
                    find('div', {'id': self._div_id}).\
                    findAll('option', {'value': re.compile(self._value_re)})
                self._cache = [self._root_url + option['value'] for option in options]
            fp.close()
        return self._cache

    @property
    def _root_url(self):
        return 'http://ngm.nationalgeographic.com'

    @abc.abstractproperty
    def _path(self):
        pass

    @abc.abstractproperty
    def _div_id(self):
        pass

    @abc.abstractproperty
    def _value_re(self):
        pass

    @abc.abstractmethod
    def _parse_photo_urls(self, contents):
        pass


class NGMLatest(NGMOrigin):
    def __init__(self):
        super(NGMLatest, self).__init__()

    @property
    def _path(self):
        return '/wallpaper'

    @property
    def _div_id(self):
        return 'entries-wallpaper'

    @property
    def _value_re(self):
        return r'^/wallpaper/\d{4}/'

    def _parse_photo_urls(self, contents):
        result = []
        gallery = BeautifulSoup(contents).find('div', {'id': 'gallery'})
        for item in gallery.findAll('a', {'target': '_blank', 'href': re.compile(r'^/wallpaper/img/')}):
            result.append(self._expand_href(self._root_url, item['href']))
        return result


class NGMArchive(NGMOrigin):
    def __init__(self):
        super(NGMArchive, self).__init__()

    @property
    def _path(self):
        return '/wallpaper/download'

    @property
    def _div_id(self):
        return 'gallery_middle_content'

    @property
    def _value_re(self):
        return r'^/wallpaper/\d{4}/.*\.xml$'

    def _parse_photo_urls(self, contents):
        result = []
        root = ElementTree.fromstring(contents)
        for photo in root.findall('photo'):
            wallpaper = photo.find('wallpaper')
            url = \
                wallpaper.text.strip() or \
                wallpaper[-1].text.strip()
            if url:
                result.append(self._expand_href(self._root_url, url))
        return result


class MiscellaneousGalleriesOrigin(LeafOrigin):
    def __init__(self, urls):
        super(MiscellaneousGalleriesOrigin, self).__init__()
        self._urls = urls

    @property
    def photo(self):
        # Initializations.
        gallery_url = random.choice(self._urls)
        wallpaper_url = None
        result = None

        # Select random wallpaper page URL from gallery.
        fp = urllib2.urlopen(gallery_url, None, self._timeout)
        if fp.getcode() == 200:
            options = []

            json_obj =  json.loads(
                            BeautifulSoup(fp.read()).\
                            find('div', { "data-pestle-module": "PresentationMode" }).\
                            find('script').string
                        )
            items = json_obj['json']['items'][0]['items']

            for item in items:
                options.append(item['url'])

            if len(options) > 0:
                wallpaper_url = self._expand_href(gallery_url, random.choice(options))

        fp.close()

        # Fetch wallpaper page URL and extract image URL.
        if wallpaper_url is not None:
            fp = urllib2.urlopen(wallpaper_url, None, self._timeout)
            if fp.getcode() == 200:
                result = {
                    'index': gallery_url,
                    'url': wallpaper_url
                }
            fp.close()

        # Done!
        return result


class ComposedOrigin(Origin):
    __metaclass__ = abc.ABCMeta

    def __init__(self, origins):
        super(ComposedOrigin, self).__init__()
        self._origins = origins

    @property
    def photo(self):
        result = None
        if self._origins:
            result = random.choice(self._origins).photo
        return result
