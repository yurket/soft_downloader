#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from sys import argv

from HTMLParser import HTMLParser, HTMLParseError

import urllib2
import urlparse
import pickle

DEBUG_MODE = False

def DBG(m1, arg):
    if DEBUG_MODE:
        print("__DBG: %r : %r" %(m1,arg))


class LinksCollector(HTMLParser):
    links = dict()
    a_tag_encounered = False

    def get_links_dict(self):
        return self.links

    def get_attr_val(self, t, key = 'href'):
        """returns value of href attribute"""
        for x in t:
            if x[0] == key:
                return x[1]     # url, if x[0] is 'href'
        return None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            self.a_tag_encounered = True
            self.current_a_href = self.get_attr_val(attrs, 'href')
            self.links.update({self.current_a_href: ''})
            DBG('self.current_a_href', self.current_a_href)

    def handle_data(self, data):
        DBG('data', data)
        if self.a_tag_encounered:
            self.links.update({self.current_a_href: data})
            DBG('\t updating with data %s', data)

    def handle_endtag(self, tag):
        if tag == 'a':
            self.a_tag_encounered = False

    def handle_startendtag(self, tag, attrs):
        DBG('handle_startendtag: tag: %s', tag)
        DBG('attrs: %s', str(attrs))
        if tag == 'a':
            href = self.get_attr_val(attrs, 'href')
            self.links.update({href: ''})

    def __repr__(self):
        info = 'All collected links: \n'
        for key, val in self.links.iteritems():
            info += '\t%r: %r\n' % (key, val)
        return info


class WebSite():
    """An abstract class for such types of sites, which provide id and software version correspondence.
   '/download_google_chrome/13800/': 'Google Chrome 24.0.1312.27 Beta'
   '/download_google_chrome/14397/': 'Google Chrome 25.0.1364.97' and so on."""
    MAX_ID = 100
    DATA_CHUNK_SIZE = 2**19             # 512 KB
    links_to_files = dict()

    def __init__(self, url, download_page_trait, file_link_trait):
        self.start_url = url
        self.download_page_trait = download_page_trait
        self.file_link_trait = file_link_trait

    def collect_links_by_trait(self, url, trait):
        parser = LinksCollector()
        try:
            parser.feed(urllib2.urlopen(url).read())
            parser.close()
        except Exception as ex:
            print(ex)
        
        all_links = parser.get_links_dict()
        collected = dict()
        for k,v in all_links.iteritems():
            if k.find(trait) != -1:
                collected.update({k: v})
        return collected

    def collect_links_to_files(self):
        download_pages = self.collect_links_by_trait(self.start_url, self.download_page_trait)
        for url, name in download_pages.iteritems():
            self.links_to_files.update(self.collect_links_by_trait(url, self.file_link_trait))

    def dump_links_to_files(self, name = 'file_links.dump'):
        pickle.dump(self.links_to_files, open(name, 'wb'))

    def get_links_to_files(self):
        return self.links_to_files

    def __repr__(self):
        repr_str = 'links to files:\n'
        for k, v in self.links_to_files.iteritems():
            repr_str += '\t%s: %s\n' % (k,v)
        return repr_str


class SoftDownloader:
    def __init__(self, url, save_dir = '.'):
        self.site = WebSite(url)
        self.save_dir = save_dir

    def set_save_dir(new_save_dir):
        self.save_dir = new_save_dir

    def download():
        pass

        
if __name__ == '__main__': 

    old_apps = WebSite('http://www.oldapps.com/google_chrome.php', '?download', 'app=')
    old_apps.collect_links_to_files()
    print(old_apps)
    old_apps.dump_links_to_files()