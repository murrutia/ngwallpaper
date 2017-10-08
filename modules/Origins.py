#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
from __future__ import with_statement

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
from contextlib import closing
from xml.etree import ElementTree
from BeautifulSoup import BeautifulSoup

import Script
import KnownOrigins

# used to call dynamically any class from this module with `getattr(Origins, 'className')()`
Origins = sys.modules[__name__]

HTTP_TIMEOUT = 30
EXTENSIONS = ['.jpg', '.jpeg', '.png', 'tiff', 'tif']
FILENAMEBASE = 'ngwallpaper'

class Origin(object):
    ''' Meta-class for the origins (repositories) of wallpapers '''
    __metaclass__ = abc.ABCMeta

    def __init__(self):
        pass

    @abc.abstractproperty
    def photo(self):
        pass

    @abc.abstractproperty
    def photos(self):
        pass

    @abc.abstractproperty
    def filename_base(self):
        pass

    @abc.abstractmethod
    def clear_cache(self):
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
        if len(self._origins) > 0:
            origin = random.choice(self._origins)
            result = origin.photo
        return result

    @property
    def photos(self):
        result = []
        for origin in self._origins:
            result += origin.photos
        return result

    @property
    def filename_base(self):
        filename_bases = []
        for origin in self._origins:
            filename_bases += origin.filename_base
        return filename_bases

    def clear_cache(self):
        for origin in self._origins:
            origin.clear_cache()

    def addOrigin(self, origin):
        self._origins.append(origin)
        return self

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
        self._cache = None

    @property
    def photo(self):
        result = None
        if len(self.photos) > 0:
            result = random.choice(self.photos)
        return result

    @property
    def photos(self):
        if not self._cache:
            html = self._download_gallery()
            self._cache = []
            self._parse_photo_urls(html)
        return self._cache

    @property
    def filename_base(self):
        return FILENAMEBASE +'-'+ self.identifier +'-'

    def clear_cache(self):
        os.remove(self._cache_filepath)

    def _add_photo(self, photo_info):
        if photo_info.is_image:
            self._cache.append(photo_info)
        else:
            print "Domain "+ photo_info.domain +" : the url extracted doesn't seem to be an image ["+ photo_info.url +"]"

    @property
    def download_delay(self):
        return HTTP_TIMEOUT / 1000

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
    def _cache_filepath(self):
        return '/tmp/'+ self.filename_base + hashlib.sha256(self._url).hexdigest().encode('utf-8') +'.html'

    @property
    def _slug(self):
        return self.name.replace('/', '_')

    @property
    def identifier(self):
        return self.class_name +'-'+ self._slug

    @abc.abstractmethod
    def _parse_photo_urls(self, html):
        pass

    def _download_gallery(self, force=False):
        cache = self._cache_filepath
        html = ''
        if not os.path.isfile(cache) or time.time() - os.path.getmtime(cache) > self._cache_timeout:
            try:
                print "downloading "+ self._url +"..."
                time.sleep(self.download_delay)
                ifp = urllib2.urlopen(self._url, None, self._timeout)
                assert \
                    ifp.getcode() == 200, \
                    'Error while downloading gallery page : '+ self._url
                html = ifp.read()
                ifp.close()
                with open(cache, 'w') as ofp:
                    ofp.write(html)
            except Exception as e:
                print e

        else:
            print "getting from cache the page at "+ self._url
            with open(cache, 'r') as ifp:
                html = ifp.read()
        return html

    def expand_href(self, href):
        if href.startswith('http://') or href.startswith('https://'):
            return href
        elif href.startswith('//'):
            return 'http:' + href
        else:
            parsed = urlparse.urlparse(self._root_url)
            return parsed.scheme + '://' + parsed.netloc + href

class RedditOrigin(LeafOrigin):

    @property
    def _root_url(self):
        return 'https://www.reddit.com/'

    @property
    def download_delay(self):
        return 2 # Reddit imposes a 2s delay between downloads to avoid being seen as a bot

    def _parse_photo_urls(self, html):
        result = []
        entries = BeautifulSoup(html).findAll('div', {'class':re.compile('entry *')})
        for entry in entries:
            url = None
            domain = entry.find('span', { 'class': 'domain' }).find('a').string

            if domain == 'i.redd.it':
                cachedhtml = entry.find('div', { 'class': 'expando expando-uninitialized' })['data-cachedhtml']
                url = re.search('https:\/\/i\.redd\.it\/[^"]*', cachedhtml).group(0)

            elif domain == 'flickr.com':
                page = entry.find('a', { 'class': re.compile('title *') })['href']
                with closing(urllib2.urlopen(page)) as page_fp:
                    image_container = BeautifulSoup(page_fp.read()).find('meta', { 'property': 'og:image'})
                    if image_container:
                        url = image_container['content']
                        url = url.replace('_b.', '_h.') # hd version of the image ends with '**_h.jpg'
                    else:
                        Script.print_error('The image container was not found for [%(url)s]' % { 'url': page})

            elif domain == 'imgur.com':
                page = entry.find('a', { 'class': re.compile('title *') })['href']
                with closing(urllib2.urlopen(page)) as page_fp:
                    image_container = BeautifulSoup(page_fp.read()).find('div', { 'class': re.compile('post-image.*')})
                    if image_container:
                        url = image_container.find('a')['href']
                    else:
                        Script.print_error('The image container was not found for [%(url)s]' % { 'url': page})

            elif domain == 'www.artstation.com':
                page = entry.find('a', { 'class': re.compile('title *') })['href']
                with closing(urllib2.urlopen(page)) as page_fp:
                    image_container = BeautifulSoup(page_fp.read()).find('div', { 'class': 'artwork-image'})
                    if image_container:
                        url = image_container.find('img')['src']
                    else:
                        Script.print_error('The image container was not found for [%(url)s]' % { 'url': page})

            elif re.match('.*deviantart\..*', domain):
                image_container = entry.find('a', { 'class': re.compile('title *') })
                page = image_container['href']
                if PhotoInfo.is_an_image(page):
                    url = page
                else:
                    with closing(urllib2.urlopen(page)) as page_fp:
                        image_container = BeautifulSoup(page_fp.read()).find('img', { 'class': re.compile('dev-content-full ')})
                        if image_container:
                            url = image_container['src']

            else:
                url = entry.find('a', { 'class': re.compile('title *') })['href']

            if url:
                photo_info = PhotoInfo(url, self)
                self._add_photo(photo_info)

        print
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

    def __init__(self, name, composed=True):
        super(NGMOrigin, self).__init__(name=name)
        self.composed = composed

    @property
    def photos(self):
        if self.composed:
            if not self._origins:
                self._origins = ComposedOrigin()
                html = self._download_gallery()
                options = BeautifulSoup(html).\
                    find('div', {'id': self._div_id}).\
                    findAll('option', {'value': re.compile(self._value_re)})
                for option in options:
                    origin = getattr(Origins, self.class_name)(name=option[value], composed=False)
                    self._origins.addOrigin(origin)
            return self._origins.photos

        return super(NGMOrigin, self).photos

    @property
    def filename_base(self):
        if self.composed:
            filename_bases = []
            for origin in self._origins:
                filename_bases += origin.filename_base
            return filename_bases

        return super(NGMOrigin, self).filename_base

    def clear_cache(self):
        if self.composed:
            for origin in self._origins:
                origin.clear_cache()
        super(NGMOrigin, self).clear_cache()

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
    def __init__(self, name='wallpaper', composed=True):
        super(NGMLatest, self).__init__(name=name, composed=composed)

    @property
    def _div_id(self):
        return 'entries-wallpaper'

    @property
    def _value_re(self):
        return r'^/wallpaper/\d{4}/'

    def _parse_photo_urls(self, contents, index):
        gallery = BeautifulSoup(contents).find('div', {'id': 'gallery'})
        for item in gallery.findAll('a', {'target': '_blank', 'href': re.compile(r'^/wallpaper/img/')}):
            photo_info = PhotoInfo(item['href'], self)
            self._add_photo(photo_info)

class NGMArchive(NGMOrigin):
    def __init__(self, name='wallpaper/download', composed=True):
        super(NGMArchive, self).__init__(name=name, composed=composed)


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
                photo_info = PhotoInfo(url, self)
                result.append(photo_info)
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
            photo_info = PhotoInfo(item['url'], self)
            photos.append(photo_info)

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

class PhotoInfo(object):
    def __init__(self, url, origin):
        super(PhotoInfo, self).__init__()
        self.origin = origin
        self.url = url
        self.destination = ''
        self.mime_type = ''
        self.width = 0
        self.height = 0
        self._extension = None
        self._basename = None
        self._filename = None
        self._domain = None

    @property
    def url(self):
        return self._url

    @url.setter
    def url(self, url):
        url = self.origin.expand_href(url)
        self._url = re.sub(r'(.*)[?#].*$', r'\1', url)

    @property
    def extension(self):
        if not self._extension:
            self._extension = os.path.splitext(self.url)[1].lower()
        return self._extension

    @property
    def is_image(self):
        return self.extension in EXTENSIONS

    @staticmethod
    def is_an_image(filepath):
        return os.path.splitext(filepath)[1].lower() in EXTENSIONS

    @property
    def basename(self):
        if not self._basename:
            self._basename = self.filename + self.extension
        return self._basename

    @property
    def filename(self):
        if not self._filename:
            self._filename = self.origin.filename_base
            self._filename += hashlib.sha256(self.url).hexdigest()
        return self._filename

    @property
    def domain(self):
        if not self._domain:
            self._domain = urlparse.urlparse(self.url).netloc
        return self._domain

    @property
    def filepath(self):
        return os.path.join(self.destination, self.basename)

    def respects_dimensions(self, dimensions):
        return self.width > dimensions[0] and self.height > dimensions[1]

    def __str__(self):
        return json.dumps({
            'url': self.url,
            'basename': self.basename,
            'origin': self.origin.identifier,
            'domain': self.domain
        }, ensure_ascii = False)
