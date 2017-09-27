#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import

import os
import re
import abc
import sys
import json
import time
import random
import hashlib
import urllib2
import urlparse
from xml.etree import ElementTree
from BeautifulSoup import BeautifulSoup

import KnownOrigins

# used to call dynamically any class from this module with `getattr(Origins, 'className')()`
Origins = sys.modules[__name__]

HTTP_TIMEOUT = 30

class Origin(object):
    ''' Meta-class for the origins (repositories) of wallpapers '''
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractproperty
    def photo(self):
        pass

    @property
    def class_name(self):
        return self.__class__.__name__

class ComposedOrigin(Origin):
    ''' Get one wallpaper from multiple origins '''

    def __init__(self, origins=[]):
        super(ComposedOrigin, self).__init__()
        self._origins = origins

    @property
    def photo(self):
        result = None
        if self._origins:
            origin = random.choice(self._origins)
            result = origin.photo
        return result

    def addOriginDefinitions(self, origin_definitions):
        for origin_definition in origin_definitions:
            origin = self._constructOrigin(origin_definition)
            self._origins.append(origin)
        return self

    def _constructOrigin(self, origin_definition):
        name = origin_definition['name']
        obj = getattr(Origins, origin_definition['class'])(name)
        return obj


class LeafOrigin(Origin):
    ''' Meta-class for origins leaves. Get one wallpaper from one origin '''

    def __init__(self, name):
        super(LeafOrigin, self).__init__()
        self.name = name
        self._cache = []

    @property
    def photo(self):
        result = None
        if self._photos:
            result = random.choice(self._photos)
            result['origin'] = self.class_name
            result['name'] = self.name
        return result

    @abc.abstractproperty
    def _root_url(self):
        pass

    @property
    def _path(self):
        return self.name

    @property
    def _url(self):
        return self._root_url + self._path

    @property
    def _timeout(self):
        return HTTP_TIMEOUT

    @property
    def _cache_timeout(self):
        return 3600 * 24 * 30

    @property
    def _cache_filename(self):
        return '/tmp/ngwallpaper-'+ hashlib.sha256(self._url).hexdigest() +'.html'


    @property
    def _photos(self):
        if len(self._cache) <= 0:
            html = self._download_gallery()
            self._cache = self._parse_photo_urls(html)
        return self._cache

    @abc.abstractmethod
    def _parse_photo_urls(self, html):
        pass

    def _download_gallery(self, force=False):
        cache = self._cache_filename
        html = ''
        if not os.path.isfile(cache) or time.time() - os.path.getmtime(cache) > self._cache_timeout:
            ifp = urllib2.urlopen(self._url, None, self._timeout)
            assert \
                ifp.getcode() == 200, \
                'Error while downloading gallery page : '+ self._url
            html = ifp.read()
            ifp.close()
            with open(cache, 'w') as ofp:
                ofp.write(html)
        else:
            with open(cache, 'r') as ifp:
                html = ifp.read()
        return html

    def _expand_href(self, url, href):
        if href.startswith('http://') or href.startswith('https://'):
            return href
        elif href.startswith('//'):
            return 'http:' + href
        else:
            parsed = urlparse.urlparse(url)
            return parsed.scheme + '://' + parsed.netloc + href

class RedditOrigin(LeafOrigin):

    @property
    def _root_url(self):
        return 'https://www.reddit.com/'

    @property
    def _cache_timeout(self):
        # the reddit pages are updated much more frequently than the one from NGM, so we reduce the cache timeout
        return 3600

    def _parse_photo_urls(self, html):
        result = []
        entries = BeautifulSoup(html).findAll('div', {'class':re.compile('entry *')})
        for entry in entries:
            print entry
            print
            domain = entry.find('a', { 'href': re.compile('/domain/*') }).string
            if re.match('.*imgur.*', domain): # for now, only imgur domains are accepted, but it should expand to others in the future
                url = entry.find('a', { 'class': re.compile('title *') })['href']
                result.append({'url': url, 'domain': domain})
        return result

class RedditSubOrigin(RedditOrigin):

    @property
    def _path(self):
        return 'r/'+ self.name

class RedditUserOrigin(RedditOrigin):

    @property
    def _path(self):
        return 'u/'+ self.name

class NGMOrigin(LeafOrigin):

    @property
    def _photos(self):
        photos = None

        if not self._cache:
            html = self._download_gallery()
            options = BeautifulSoup(html).\
                find('div', {'id': self._div_id}).\
                findAll('option', {'value': re.compile(self._value_re)})
            self._cache = [self._root_url + option['value'] for option in options]

        index = random.choice(self._cache)
        fp = urllib2.urlopen(index, None, self._timeout)
        if fp.getcode() == 200:
            photos = self._parse_photo_urls(fp.read())

        return photos

    @property
    def _root_url(self):
        return 'http://ngm.nationalgeographic.com/'

    @abc.abstractproperty
    def _div_id(self):
        pass

    @abc.abstractproperty
    def _value_re(self):
        pass

class NGMLatest(NGMOrigin):
    def __init__(self, name='wallpaper'):
        super(NGMLatest, self).__init__(name=name)

    @property
    def _div_id(self):
        return 'entries-wallpaper'

    @property
    def _value_re(self):
        return r'^/wallpaper/\d{4}/'

    def _parse_photo_urls(self, contents, index):
        result = []
        gallery = BeautifulSoup(contents).find('div', {'id': 'gallery'})
        for item in gallery.findAll('a', {'target': '_blank', 'href': re.compile(r'^/wallpaper/img/')}):
            result.append({
                'index': index,
                'url': self._expand_href(self._root_url, item['href'])
            })
        return result


class NGMArchive(NGMOrigin):
    def __init__(self, name='wallpaper/download'):
        super(NGMArchive, self).__init__(name=name)

    @property
    def _div_id(self):
        return 'gallery_middle_content'

    @property
    def _value_re(self):
        return r'^/wallpaper/\d{4}/.*\.xml$'

    def _parse_photo_urls(self, contents, index):
        result = []
        root = ElementTree.fromstring(contents)
        for photo in root.findall('photo'):
            wallpaper = photo.find('wallpaper')
            url = wallpaper.text.strip() or wallpaper[-1].text.strip()
            if url:
                result.append({
                    'index': index,
                    'url': self._expand_href(self._root_url, url)
                })
        return result


class NGMGalleryOrigin(LeafOrigin):

    @abc.abstractproperty
    def _root_url(self):
        pass

    def _parse_photo_urls(self, html):
        photos = []
        json_obj =  json.loads(
                        BeautifulSoup(html).\
                        find('div', { "data-pestle-module": "PresentationMode" }).\
                        find('script').string
                    )
        items = json_obj['json']['items'][0]['items']

        for item in items:
            url = self._expand_href(self._url, item['url'])
            photos.append({ 'url': url })

        return photos

class NGMGalleryPhotographyOrigin(NGMGalleryOrigin):
    @property
    def _root_url(self):
        return 'http://photography.nationalgeographic.com/photography/photos/'

class NGMGalleryAnimalsOrigin(NGMGalleryOrigin):
    @property
    def _root_url(self):
        return 'http://animals.nationalgeographic.com/animals/photos/'

class NGMGalleryAdventureOrigin(NGMGalleryOrigin):
    @property
    def _root_url(self):
        return 'http://adventure.nationalgeographic.com/adventure/'
