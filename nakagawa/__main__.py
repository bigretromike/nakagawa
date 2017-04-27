#!/usr/bin/env python
# -*- coding: utf-8 -*-

import nakagawa
import time

print("Nakagawa init...")
n = nakagawa.Nakagawa()

while True:
    print("{}".format(str(time.time())))
    n.check_wallabag()
    n.check_4chan()
    n.watch_4chan()
    time.sleep(300)  # 5minute sleep
