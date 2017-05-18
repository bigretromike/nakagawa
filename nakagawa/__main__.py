#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nakagawa
import time

n = nakagawa.Nakagawa()
n.logger.info("Nakagawa: starting")

while True:
    n.logger.info(time.strftime("%d-%m-%Y %H:%M:%S"))
    n.logger.debug("wallabag: checking")
    n.check_wallabag()
    n.logger.debug("4chan: checking")
    n.check_4chan()
    n.logger.debug("4chan: watching")
    n.watch_4chan()
    time.sleep(300)  # 5minute sleep
