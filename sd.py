#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from os import getcwd
from sys import argv

from HTMLParser import HTMLParser

import urllib2
import urlparse

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
            DBG('self.current_a_href', self.current_a_href)

    def handle_data(self, data):
        if self.a_tag_encounered:
            self.links.update({self.current_a_href: data})
            DBG('\t updating with data %s', data)


    def handle_endtag(self, tag):
        if tag == 'a':
            self.a_tag_encounered = False


    def __repr__(self):
        info = 'All collected links: \n'
        for key in self.links.keys():
            info += '\t%r: %r\n' % (key, self.links[key])
        # for x in self.links:
        #     info += '%r\n' % x
        return info


class WebSite():
    def __init__(self, url):
        self.url = url
        try:
            self.body = urllib2.urlopen(self.url).read()
        except Exception, e:
            print(e)
            self.body = ''
        

    def get_all_links(self):
        pass
        
    def __repr__(self):
        return "site body:" + str(self.body)

class SoftDownloader:
    def __init__(self, url, save_dir = '.'):
        self.site = WebSite(url)
        self.save_dir = save_dir

    def set_save_dir(new_save_dir):
        self.save_dir = new_save_dir

    def download():
        pass

        


def main():
    parser = LinksCollector()
    parser.feed(urllib2.urlopen('http://www.oldapps.com/nokia_suite.php?old_nokia_pc_suite=1?download').read())
    print(parser)




if __name__ == '__main__':
    main()