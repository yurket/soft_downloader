#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os
import sys
import urllib2
import shutil
import threading
import time

from sd import LinksCollector, DBG

class MyLogger():
    LOGGINING_ENABLE = True
    def __init__(self, logname = "log.txt"):
        self.LOG_NAME = os.path.dirname(__file__) + os.sep + logname
        if os.path.exists(self.LOG_NAME):
            shutil.move(self.LOG_NAME, self.LOG_NAME + '.old')
        print('logname: %s' % self.LOG_NAME)

    def Log(self, msg):
        if self.LOGGINING_ENABLE:
            msg = str(time.strftime("%H:%M:%S")) + ' - ' + msg 
            print(msg)
            with open(self.LOG_NAME, 'ab') as f:
                f.write(msg)

    def pause_logging(self):
        self.LOGGINING_ENABLE = False
    def resume_logging(self):
        self.LOGGINING_ENABLE = True

    def __repr__(self):
        return self


class OldAppsDownloader():
    """Works only with oldapps.com. Just goes through the links and try to download files
    expects on input url kindof http://www.oldapps.com/nokia_suite.php?old_nokia_pc_suite= """
    MAX_ID = 50
    DATA_CHUNK_SIZE = 2**19     # 512 KB
    targets = dict()
    TARGETS_LOCK = threading.Lock()

    def __init__(self, url):
        self.start_url = url
        self.logger = MyLogger()
        
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
                    self.logger.Log('checking id ' + str(id_counter))
                continue
            parser = LinksCollector()
            parser.feed(reply.read())
            file_info = self.find_app_link(parser.get_links_dict())

            self.TARGETS_LOCK.acquire()
            self.targets.update(file_info)
            self.TARGETS_LOCK.release()

    def downloader(self):
        time.sleep(5)
        worker = threading.Thread(target=self.download_files())

    def download_files(self):
        if len(self.targets) == 0:
            return 0

        self.logger.Log(self.__repr__())
        while len(self.targets) > 0:
            self.TARGETS_LOCK.acquire()
            url, name = self.targets.popitem()
            self.TARGETS_LOCK.release()

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

    downloader = OldAppsDownloader(url)
    downloader.find_files_urls()
    downloader.downloader()


