#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# -*- mode: Python; tab-width: 4; indent-tabs-mode: nil; -*-
# Do not change the previous lines. See PEP 8, PEP 263.
"""
ComicStreamer main server classes

Copyright 2012-2014  Anthony Beville

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

	http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import logging
import logging.handlers
import os
import platform
import signal
import sys

import comicstreamerlib.utils
from comicstreamerlib.bonjour import BonjourThread
from comicstreamerlib.config import ComicStreamerConfig
from comicstreamerlib.folders import AppFolders
from comicstreamerlib.options import Options
from comicstreamerlib.server import APIServer


class Launcher:
    def signal_handler(self):
        logging.info("Caught Ctrl-C or SIGTERM.  exiting.")
        if self.apiServer:
            self.apiServer.shutdown()
        sys.exit()

    def go(self):
        # Configure logging
        # root level
        logger = logging.getLogger()
        logger.setLevel(logging.DEBUG)

        # By default only do info level to console
        sh = logging.StreamHandler()
        sh.setLevel(logging.INFO)
        logger.addHandler(sh)

        comicstreamerlib.utils.fix_output_encoding()
        self.apiServer = None

        opts = Options()
        opts.parseCmdLineArgs()
        # turn up the console log level, if requested
        if opts.debug:
            sh.setLevel(logging.DEBUG)
        elif opts.quiet:
            sh.setLevel(logging.CRITICAL)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        sh.setFormatter(formatter)

        log_file = os.path.join(AppFolders.logs(), "ComicStreamer.log")
        if not os.path.exists(os.path.dirname(log_file)):
            os.makedirs(os.path.dirname(log_file))
        fh = logging.handlers.RotatingFileHandler(log_file, maxBytes=1048576, backupCount=4, encoding="UTF8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        config = ComicStreamerConfig()
        config.applyOptions(opts)

        self.apiServer = APIServer(config, opts)

        self.apiServer.logFileHandler = fh
        self.apiServer.logConsoleHandler = sh

        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        bonjour = BonjourThread(self.apiServer.port)
        bonjour.start()

        if getattr(sys, 'frozen', None):
            # A frozen app will run a GUI
            self.apiServer.runInThread()

            logging.info("starting GUI loop")
            if platform.system() == "Darwin":
                from gui_mac import MacGui
                MacGui(self.apiServer).run()
            elif platform.system() == "Windows":
                from gui_win import WinGui
                WinGui(self.apiServer).run()
                self.apiServer.shutdown()
        else:
            # from gui_qt import QtBasedGui
            # self.apiServer.runInThread()
            # QtBasedGui(self.apiServer).run()
            # self.apiServer.shutdown()
            self.apiServer.run()

        logging.info("GUI should be done now")


def main():
    Launcher().go()
