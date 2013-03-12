#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import urllib2

from sd import LinksCollector, DBG

ENABLE_LOGGINING = True
LOG_NAME = None

def Log(msg):
    global LOG_NAME
    if LOG_NAME is None:
        LOG_NAME = os.path.dirname(__file__) + os.sep + "log.txt"
        print('logname: %s' % LOG_NAME)
    if ENABLE_LOGGINING:
        print(msg)
        with open(LOG_NAME, 'ab') as f:
            f.write(msg)

class OldAppsDownloader():
    """Works only with oldapps.com. Just goes through the links and try to download files
    expects on input url kindof http://www.oldapps.com/nokia_suite.php?old_nokia_pc_suite= """
    MAX_ID = 50
    DATA_CHUNK_SIZE = 2**19     # 512 KB
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
                if id_counter % (self.MAX_ID/5) == 0:
                    Log('checking id ' + str(id_counter) + '\n')
                continue
            parser = LinksCollector()
            parser.feed(reply.read())
            file_info = self.find_app_link(parser.get_links_dict())
            self.targets.update(file_info)

    def download_files(self):
        if not self.targets:
            Log('no files coolected in this ID range!')
            return 0

        Log(self.__repr__())
        for url, name in self.targets.iteritems():
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

    def __repr__(self):
        repr_str = 'files for downloading:\n'
        for k, v in self.targets.iteritems():
            repr_str += '\t%s: %s\n' % (k,v)
        return repr_str


if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('usage: OldAppsDownloader.py dir_name url')
        sys.exit(1)
    target_dir, url = sys.argv[1], sys.argv[2]

    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    os.chdir(target_dir)

    # url = 'http://www.oldapps.com/nokia_suite.php?old_nokia_pc_suite=1?download'
    downloader = OldAppsDownloader(url)
    downloader.find_files_urls()
    downloader.download_files()


