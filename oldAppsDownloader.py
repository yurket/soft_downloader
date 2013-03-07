#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

from os import getcwd
from sys import argv

import urllib2

from sd import LinksCollector, DBG

class OldAppsDownloader():
    """Works only with oldapps.com. Just goes through the links and try to download files
    expects on input url kindof http://www.oldapps.com/nokia_suite.php?old_nokia_pc_suite= """
    MAX_ID = 10
    targets = dict()
    def __init__(self, url):
        self.start_url = url
        
    def find_app_link(self, d):
        for url in d.iterkeys():
            if url.find('?app=') != -1:
                return {url: d[url]}
        return None

    def find_files_urls(self):
        for id_counter in xrange(1, self.MAX_ID):
            url = self.start_url + str(id_counter) + '?download'
            DBG('url: ', url)
            try:
                reply = urllib2.urlopen(url)
            except urllib2.HTTPError:
                continue
            parser = LinksCollector()
            parser.feed(reply.read())
            file_info = self.find_app_link(parser.get_links_dict())
            self.targets.update(file_info)

    def download_files(self):
        if not self.targets:
            print('no files coolected in this ID range!')
            return 0
        print(self.targets)
        for url, name in self.targets.iteritems():
            with open(name + '.bin', "wb") as f:
                try:
                    reply = urllib2.urlopen(url)
                except Exception, e:
                    print(e)
                f.write(reply.read())




if __name__ == '__main__':
    downloader = OldAppsDownloader('http://www.oldapps.com/camfrog.php?old_camfrog=')
    downloader.find_files_urls()
    downloader.download_files()


