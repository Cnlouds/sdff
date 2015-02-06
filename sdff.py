#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
This is a script to use find sensitive dir and file
"""

__author__ = 'piaca'
__version__ = '0.1'

import sys
import Queue
import hashlib
import argparse
import threading 

import requests
import threadpool

from color import *


def parse_args():
    parser = argparse.ArgumentParser(version='0.1', description='This is a script use to find sensitive dir and file')
    parser.add_argument('-u', action='store', dest='url', help='the url of target')
    return parser

class SDFF(object):
    """
    """
    def __init__(self, url):
        self.url = self.parse_url(url)

        # dir and file dict 
        self.dir_filename = "dir.txt"
        self.file_filename = "file.txt"

        self.dir_queue = []
        self.sensitive_dir = ['/']
        self.file_queue = []
        self.sensitive_file = []

        self.timeout = 5
        self.max_threads = 10 

        self.lock = threading.Lock()

        # requests
        self.req = requests.Session()
        self.req.headers.update({
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2269.0 Safari/537.36"
        })

    def parse_url(self, url):
        if url[-1] == '/':
            return url[:-1]
        return url

    def get_dir_content(self):
        dir_contents = open(self.dir_filename, 'r').readlines()
        self.dir_queue = [dir_content.strip() for dir_content in dir_contents if dir_content.strip() != ""]

    def get_file_content(self):
        file_contents = open(self.file_filename, 'r').readlines()
        self.file_queue = [file_content.strip() for file_content in file_contents if file_content.strip() != ""]

    def get_error_hash(self, url):
        url = "{0}/woyouyitouxiaomaolv.txt".format(url)
        try:
            resp = self.req.get(url, timeout=self.timeout)
            return hashlib.md5(resp.content).hexdigest()
        except:
            return None

    def dir_finder(self, base_url, dir_name):
        dir_url = "{0}{1}".format(base_url, dir_name)
        try:
            resp = self.req.get(dir_url, allow_redirects=False, timeout=self.timeout)
            if resp.status_code in (301, 302) and resp.headers['location'] == '{0}/'.format(resp.url):
                self.lock.acquire()
                cprint(BLUE, dir_name)
                self.sensitive_dir.append(dir_name)
                self.lock.release()
        except Exception, e:
            print e

    def file_finder(self, error_hash, base_url, dir_name, file_name):
        for _dir_name in dir_name:
            file_url = "{0}{1}{2}".format(base_url, _dir_name, file_name)
            try:
                resp = self.req.get(file_url, timeout=self.timeout)
                if resp.status_code == 200 and hashlib.md5(resp.content).hexdigest() != error_hash:
                    self.lock.acquire()
                    cprint(BLUE, '{0}{1}'.format(_dir_name, file_name))
                    self.sensitive_file.append('{0}{1}'.format(_dir_name, file_name))
                    self.lock.release()
            except:
                pass

    def exploit(self):

        # load dir dict
        self.get_dir_content()

        # load file dict
        self.get_file_content()

        # get error page md5 hash
        self.error_hash = self.get_error_hash(self.url)

        # create thread pool, set thread num is 10, and burteforce dir name
        pool = threadpool.ThreadPool(self.max_threads)
        for dir_name in self.dir_queue:
            pool.add_task(self.dir_finder, self.url, dir_name)
        pool.destroy()

        # create thread pool, set thread num is 10, and burteforce file name
        pool = threadpool.ThreadPool(self.max_threads)
        for file_name in self.file_queue:
            pool.add_task(self.file_finder, self.error_hash, self.url, self.sensitive_dir, file_name)
        pool.destroy()

if __name__ == '__main__':
    parser = parse_args()
    args = parser.parse_args()
    if args.url == None:
        parser.print_help()
        sys.exit(1)
    url = args.url

    sdff = SDFF(url)
    sdff.exploit()