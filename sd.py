#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import sys
import os
import shutil
import time
import string
from HTMLParser import HTMLParser, HTMLParseError

import urllib2
import pickle

DEBUG_MODE = False

def DBG(m1, arg):
    if DEBUG_MODE:
        print("__DBG: %r : %r" %(m1,arg))
def DBGS(debug_string, end='\n'):
    print(debug_string, end=end)

class MyLogger():
    LOGGINING_ENABLE = True

    def __init__(self, logname = "log.txt"):
        # self.LOG_NAME = os.path.dirname(__file__) + os.sep + logname
        self.LOG_NAME = os.path.abspath(os.getcwd()) + os.sep + logname
        if os.path.exists(self.LOG_NAME):
            shutil.move(self.LOG_NAME, self.LOG_NAME + '.old')
        print('logname: %s' % self.LOG_NAME)

    def Log(self, msg):
        if self.LOGGINING_ENABLE:
            msg = str(time.strftime("%H:%M:%S")) + ' - ' + msg

            print(msg)
            with open(self.LOG_NAME, 'ab') as f:
                f.write(msg + '\n')
                f.flush()

    def pause_logging(self):
        self.LOGGINING_ENABLE = False
    def resume_logging(self):
        self.LOGGINING_ENABLE = True

    def __repr__(self):
        return self

class HTMLHrefCollector(HTMLParser):
    """Parses html page and stores 'href' attribute of <a> tag in dict {'url': name_if_exists} """
    links = dict()
    a_tag_encounered = False

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
        self.url_traits = url_trait_list
        self.links_to_files = dict()
        self.logger = MyLogger()

    def collect_links_by_trait(self, url, trait):
        parser = HTMLHrefCollector()
        try:
            parser.feed(urllib2.urlopen(url).read())
            parser.close()
        except Exception as ex:
            self.logger.Log('ERROR while parsing ' + url + ': ' + str(ex))
        
        all_links = parser.get_links_dict()
        collected = dict()
        for k,v in all_links.iteritems():
            if k.find(trait) != -1:
                collected.update({k: v})
        return collected

    def collect_links_to_files(self):
        args = len(self.url_traits)
        if args == 0:
            self.logger.Log('ERROR: There is no traits!')
            return 1
        elif args == 1:
            self.links_to_files.update(self.collect_links_by_trait(self.start_url, self.url_traits[0]))
        elif args == 2:
            download_pages = self.collect_links_by_trait(self.start_url, self.url_traits[0])
            DBGS('-', end='')
            for url, name in download_pages.iteritems():
                DBGS('>', end='')
                self.links_to_files.update(self.collect_links_by_trait(url, self.url_traits[1]))
        elif args == 3:
            download_pages = self.collect_links_by_trait(self.start_url, self.url_traits[0])
            for url, name in download_pages.iteritems():
                DBGS('-', end='')
                download_pages2 = self.collect_links_by_trait(url, self.url_traits[1])
                for url, name in download_pages2:
                    DBGS('>', end='')
                    self.links_to_files.update(self.collect_links_by_trait(url, self.url_traits[2]))
        else:
            self.logger.Log('ERROR: Level for collecting links is too deep!')
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
        self.logger = MyLogger() if not site.logger else site.logger

    def set_save_dir(new_save_dir):
        self.save_dir = new_save_dir

    def download_files(self, targets = None):
        if targets == None:
            targets = self.site.get_links_to_files()

        if len(targets) == 0:
            self.logger.Log('0 links to files found -> check URL or site availability!')
            return 0

        self.logger.Log('Start downloading files')
        self.logger.Log('link count: ' + str(len(targets)))
        for url, name in targets.iteritems():
            name = name.translate(None, '/')            # get rid of '/' for Unix systems
            name = name.translate(None, string.whitespace.translate(None, ' '))    # remove whitespace, except space
            ns = name.split()       # remove sequences of spaces
            name = ' '.join(ns)

            filename = name + '.bin'
            if not os.path.exists(filename):
                with open(filename, "wb") as f:
                    try:
                        reply = urllib2.urlopen(url)
                        while True:
                            data = reply.read(self.DATA_CHUNK_SIZE)
                            if data == '':
                                break
                            f.write(data)
                    except Exception, e:
                        print(e)
            self.logger.Log('downloading ' + filename + ' (' + url + ')')

    def __repr__(self):
        return self

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('usage: sd.py dir_name url')
        print('for example: sd.py chrome http://www.oldapps.com/google_chrome.php')
        sys.exit(1)

    target_dir, url = sys.argv[1], sys.argv[2]
    traits = sys.argv[3:]
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    os.chdir(target_dir)

    if url.find('adobe.com') != -1:
        adobe = WebSite(url)
        links = adobe.collect_links_by_trait(url, 'archive.zip')
        sd = SoftDownloader(adobe).download_files(links)
        sys.exit(0)

    # old_apps = WebSite('http://www.oldapps.com/google_chrome.php', '?download', 'app=')
    target_site = WebSite(url, traits)
    target_site.collect_links_to_files()
    target_site.dump_links()

    sd = SoftDownloader(target_site).download_files()
