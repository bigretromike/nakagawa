#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import os
import urllib
import json
import db
import logging
from sqlalchemy import exists
from wallabag_api.wallabag import Wallabag
import basc_py4chan


class Nakagawa:
    home_dir = os.path.expanduser("~")
    cfg_dir = os.path.join(home_dir, ".nakagawa")
    cfg_file = os.path.join(cfg_dir, "nakagawa.json")
    log_file = os.path.join(cfg_dir, "nakagawa.log")
    config = {}

    def __init__(self):
        self.logger = logging.getLogger('nakagawa')
        hdlr = logging.FileHandler(self.log_file)
        formatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.logger.addHandler(hdlr)
        self.logger.setLevel(logging.INFO)

        if not os.path.exists(self.cfg_dir):
            os.mkdir(self.cfg_dir, 0o750)
        if not os.path.exists(self.cfg_file):
            self.new_config()
        self.config = json.load(open(name=self.cfg_file, mode='r'))
        db.init_db(self.config['database'])

    def new_config(self):
        print('Creating new config file ~/.nakagawa.json')
        self.config['w_username'] = raw_input('wallabag_username:')
        self.config['w_password'] = raw_input('wallabag_password:')
        self.config['w_client_id'] = raw_input('wallabag_client_id:')
        self.config['w_client_secret'] = raw_input('wallabag_client_secret:')
        self.config['w_host'] = raw_input('wallabag_host:')

        self.config['dir_output'] = raw_input('dir_output:')

        self.config['database'] = str(os.path.join(self.cfg_dir, 'nakagawa.sqlite3'))

        json.dump(self.config, open(name=self.cfg_file, mode='w'))
        print('Config saved...')

    def check_wallabag(self):
        params = {'username': self.config['w_username'],
                  'password': self.config['w_password'],
                  'client_id': self.config['w_client_id'],
                  'client_secret': self.config['w_client_secret']}
        # get token
        token = Wallabag.get_token(host=self.config['w_host'], **params)

        wall = Wallabag(host=self.config['w_host'],
                        client_secret=self.config['w_client_secret'],
                        client_id=self.config['w_client_id'],
                        token=token)

        params = {'archive': 0,
                  'star': 0,
                  'delete': 0,
                  'sort': 'created',
                  'order': 'desc',
                  'page': 1,
                  'perPage': 30,
                  'tags': []}

        data = wall.get_entries(**params)
        for post in data['_embedded']['items']:
            if 'boards.4chan.org' in post['domain_name']:
                if not db.session.query(exists().where(db.UrlsTable.url == unicode(post['url']))).scalar():
                    self.logger.info("adding {}".format(post['url']))
                    u = db.UrlsTable()
                    u.url = unicode(post['url'])
                    db.session.add(u)
                    db.session.commit()
                    wall.delete_entries(post['id'])

    def check_4chan(self):
        known_urls = db.session.query(db.UrlsTable).all()
        self.logger.info("looking thru URLs")
        if len(known_urls) > 0:
            for url in known_urls:
                _id = re.search('(?<=thread/)\d{2,10}', url.url)
                board = re.search('(?<=boards.4chan.org/)[a-z0-9]{1,10}', url.url)
                _ID = _id.group(0)
                _BOARD = board.group(0)
                self.logger.info("found {}/{}".format(_ID, _BOARD))

                if not db.session.query(exists().where(db.ThreadTable.thread_id == _ID and db.ThreadTable.board_id == _BOARD)).scalar():
                    self.logger.info("adding {}/{}".format(_ID, _BOARD))
                    t = db.ThreadTable()
                    t.board_id = _BOARD
                    t.thread_id = _ID
                    t.err404 = 0
                    t.limit = 0
                    db.session.add(t)
                    db.session.commit()

                # removing url from urls
                self.logger.info("removing {}/{} from URLs".format(_ID, _BOARD))
                r = db.session.query(db.UrlsTable).filter_by(id=url.id).first()
                db.session.delete(r)
                db.session.flush()
                db.session.commit()

    def watch_4chan(self):
        # err404 = when thread not found
        # limit = when thread hit max image limit
        watch_urls = db.session.query(db.ThreadTable).filter_by(err404=0).filter_by(limit=0).all()
        if len(watch_urls) > 0:
            for thread in watch_urls:
                x = basc_py4chan.Board(board_name=thread.board_id, https=True)
                self.logger.info("scanning: {}/{}".format(thread.board_id, thread.thread_id))
                if x.thread_exists(thread_id=thread.thread_id):
                    y = x.get_thread(thread_id=thread.thread_id, update_if_cached=True)

                    path = self.config['dir_output']
                    if not os.path.exists(path):
                        os.mkdir(path)
                    path = os.path.join(path, thread.board_id)
                    if not os.path.exists(path):
                        os.mkdir(path)
                    path = os.path.join(path, str(thread.thread_id))
                    if not os.path.exists(path):
                        os.mkdir(path)
                        file_t = open(os.path.join(path, "topic.txt"), "w")
                        file_t.write(str(y.topic.subject))
                        file_t.close()

                    self.logger.info("downloading: {}/{}".format(thread.board_id, thread.thread_id))
                    for file_i in y.files():
                        file_n = os.path.basename(file_i)
                        if not os.path.exists(os.path.join(path, file_n)):
                            self.logger.debug("receiving: {}".format(file_n))
                            urllib.urlretrieve(url=file_i, filename=os.path.join(path, file_n))
                        else:
                            self.logger.debug("skipping: {}".format(file_n))

                    if not y.imagelimit or y.closed or y.archived or y.bumplimit:  # image limit or closed or archived
                        self.logger.info("image limit: {}/{}".format(thread.board_id, thread.thread_id))
                        thread.limit = 1
                        db.session.commit()
                else:
                    thread.err404 = 1
                    db.session.commit()
                    self.logger.info("404 Not Found: {}/{}".format(thread.board_id, thread.thread_id))
                self.logger.info("finished: {}/{}".format(thread.board_id, thread.thread_id))
        else:
            self.logger.info("No thread to watch")
