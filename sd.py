#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
import sys
import os
import string
import json
from HTMLParser import HTMLParser, HTMLParseError
from urlparse import urlparse

import urllib2
import pickle

class HTMLHrefCollector(HTMLParser, object):
    """Parses html page and stores 'href' attribute of <a> tag in dict {'url': name_if_exists} """
    def __init__(self):
        super(HTMLHrefCollector, self).__init__()
        self.links = dict()
        self.a_tag_encounered = False

    def get_links_dict(self):
        return self.links

    def get_attr_val(self, t, key = 'href'):
        """returns value of href attribute"""
        for x in t:
            if x[0] == key:
                return x[1]     # url, if x[0] is 'href'
        return ''

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.a_tag_encounered = True
            self.current_a_href = self.get_attr_val(attrs)
            if self.current_a_href != '':
                self.links.update({self.current_a_href: 'dummy_start_name'})


    def handle_data(self, data):
        if self.a_tag_encounered:
            if data.lower() == 'click here':
                data = self.current_a_href.split('/')[-1]
            self.links.update({self.current_a_href: data})
            logging.debug('\t updating with data %s', data)

    def handle_endtag(self, tag):
        if tag == 'a':
            self.a_tag_encounered = False

    def handle_startendtag(self, tag, attrs):
        logging.debug('handle_startendtag: tag: %s', tag)
        logging.debug('attrs: %s', str(attrs))
        if tag == 'a':
            href = self.get_attr_val(attrs)
            if href != '':
                self.links.update({href: 'dummy_startend_name'})

    def __repr__(self):
        info = 'All collected links: \n'
        for key, val in self.links.iteritems():
            info += '\t%r: %r\n' % (key, val)
        return info


class WebSite:
    """Stores collected links in dictionary. 
    It goes like this: 1) go to 'url' and collect all links with 'download_page_trait'
                       2) from the dict of just collected links visit each one and collect all with 'file_link_trait'  """

    def __init__(self, url, url_trait_list, download_page_trait = '?download', file_link_trait = 'app='):
        self.start_url = url
        self.url_scheme = urlparse(self.start_url).scheme
        self.domain = urlparse(self.start_url).netloc.replace('www.', '')
        self.url_traits = url_trait_list
        self.links_to_files = dict()
        logging.info('start processing %s', url)

    def absolute_url(self, to_abs):
        if to_abs.find(self.domain) == -1:      # relative path
            return self.url_scheme + '://' + self.domain + '/' + to_abs
        return to_abs

    def collect_links_by_trait(self, url, trait):
        parser = HTMLHrefCollector()
        try:
            parser.feed(urllib2.urlopen(url).read())
            parser.close()
        except Exception as ex:
            logging.error('while parsing %s: %s', url, str(ex))
        
        all_links = parser.get_links_dict()

        collected = dict()
        for k,v in all_links.iteritems():
            if k.find(trait) != -1:
                collected.update({k: v})
        return collected

    def collect_links_to_files(self):
        args = len(self.url_traits)
        if args == 0:
            logging.error('There is no traits!')
            return 1
        elif args == 1:
            links = self.collect_links_by_trait(self.start_url, self.url_traits[0])
            abs_links = dict( (self.absolute_url(k),v) for k,v in links.iteritems() )
            self.links_to_files.update(abs_links)
        elif args == 2:
            download_pages = self.collect_links_by_trait(self.start_url, self.url_traits[0])
            abs_download_pages = dict( (self.absolute_url(k),v) for k,v in download_pages.iteritems() )
            del download_pages
            for url, name in abs_download_pages.iteritems():
                links = self.collect_links_by_trait(url, self.url_traits[1])
                abs_links = dict( (self.absolute_url(k),v) for k,v in links.iteritems() )       # dict comprehension for poor ones =(
                self.links_to_files.update(abs_links)
        elif args == 3:
            download_pages = self.collect_links_by_trait(self.start_url, self.url_traits[0])
            abs_download_pages = dict( (self.absolute_url(k),v) for k,v in download_pages.iteritems() )
            del download_pages
            for url, name in abs_download_pages.iteritems():
                download_pages2 = self.collect_links_by_trait(url, self.url_traits[1])
                abs_download_pages2 = dict( (self.absolute_url(k),v) for k,v in download_pages2.iteritems() )
                del download_pages2
                for url, name in abs_download_pages2:
                    links = self.collect_links_by_trait(url, self.url_traits[2])
                    abs_links = dict( (self.absolute_url(k),v) for k,v in links.iteritems() )
                    self.links_to_files.update(abs_links)
        else:
            logging.error('Level for collecting links is too deep!')
            return 1

    def dump_links(self, name = 'file_links.dump'):
        pickle.dump(self.links_to_files, open(name, 'wb'))

    def get_links_to_files(self):
        return self.links_to_files

    def __repr__(self):
        repr_str = 'links to files:\n'
        for k, v in self.links_to_files.iteritems():
            repr_str += '\t%s: %s\n' % (k,v)
        return repr_str


class SoftDownloader:
    """Downloads files using links, that 'site' object has collected """
    DATA_CHUNK_SIZE = 2**19             # 512 KB

    def __init__(self, site, save_dir = '.'):
        self.site = site
        self.save_dir = save_dir
        if not os.path.exists(self.save_dir):
            os.mkdir(self.save_dir)

    def set_save_dir(self, new_save_dir):
        self.save_dir = new_save_dir

    def download_files(self, targets = None):
        if targets == None:
            targets = self.site.get_links_to_files()

        if len(targets) == 0:
            logging.warn('0 links to files found -> check URL or site availability!')
            return 0

        logging.info('Start downloading files into %s', str(self.save_dir))
        logging.info('link count: %d ', len(targets))
        for url, name in targets.iteritems():
            if url == None:                             # empty link (was removed from site)
                continue
            name = name.translate(None, '/')            # get rid of '/' for Unix systems
            name = name.translate(None, string.whitespace.translate(None, ' '))    # remove whitespace, except space
            ns = name.split()       # remove sequences of spaces
            name = ' '.join(ns)

            filename = self.save_dir + os.sep + name + '.bin'
            if not os.path.exists(filename):
                logging.info('downloading %s from url: %s', filename, url)
                with open(filename, "wb") as f:
                    try:
                        reply = urllib2.urlopen(url)
                        while True:
                            data = reply.read(self.DATA_CHUNK_SIZE)
                            if data == '':
                                break
                            f.write(data)
                            print('.', end='')
                        print()
                    except Exception, e:
                        print(e)

    def __repr__(self):
        return self

class Controller:
    """
    Loads json db with urls and arguments.
    After collects links and downloads files for every entry
    """
    def __init__(self, config_filename):
        try:
            with open(config_filename, 'rb') as db:
                self.sites = json.load(db)
        except Exception as ex:
            print(ex)               # log instead

    def process_entries(self):
        for entry in self.sites:
            target_site = WebSite(entry['url'], entry['traits'])
            target_site.collect_links_to_files()
            target_site.dump_links()

            sd = SoftDownloader(target_site, entry['dst_folder'])
            sd.download_files()

    def __repr__(self):
        return self


if __name__ == '__main__':
    logging.basicConfig(filename='sd.log', level=logging.INFO,\
                        format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %I:%M:%S %p')
    logging.info('[STARTED]')
    if len(sys.argv) < 2:
        print('usage: sd.py db_path')
        sys.exit(1)

    db_filename = sys.argv[1]
    c = Controller(db_filename)
    c.process_entries()
    logging.info('[FINISHED]')