#!/usr/bin/env python
# -*- coding: utf-8 -*-
import argparse
import logging
import time
import os
import sys
from argparse import ArgumentParser
from watchdog.observers import Observer
from watchdog.events import LoggingEventHandler
from watchdog.events import (
    FileSystemEventHandler,
    FileModifiedEvent,
    FileDeletedEvent,
    FileCreatedEvent
)

logger = logging.getLogger(__name__)

class RsyncJob(LoggingEventHandler):
    logger = logging.getLogger('RsyncJob')
    syncing = False
    
    def __init__(self, observer, args ):
        self.source = args.source.rstrip('/') + '/'

        self.dest = ''
        self.dest += args.user + '@' if args.user else ''
        self.dest += args.host + ':' if args.host else ''
        self.dest += args.dest or self.source
    
        self.exclude = ''
        if args.type:
            if args.type == 'git':
                self.exclude = '--exclude-from=- <<EOF\n.git/\n.DS_Store\n.project\n.pydevproject\nREADME.md\nEOF'
        
        observer.schedule( self, self.source, recursive=True )
                
    def sync(self):
        self.syncing = True
        self.logger.info( 'syncing {} to {}'.format( self.source, self.dest ) )
        command = 'rsync -avz {} {} {}'.format( self.source, self.dest, self.exclude )
        self.logger.debug( command )
        os.system( command )
        self.syncing = False
    
    def on_any_event(self, event):
        self.logger.debug( event.src_path )
        if not self.syncing:
            time.sleep( 2 )
            if not self.syncing:
                self.sync()

if __name__ == '__main__':
    parser = argparse.ArgumentParser( formatter_class=argparse.ArgumentDefaultsHelpFormatter )
    parser.add_argument( 'source', action='store',help='source directory to be sync`ed')    
    parser.add_argument('-H', '--host', action='store', default=None, help='destination host')
    parser.add_argument('-d','--dest', action='store', default=None, help='destination directory on remote host. per default sync`s to directory given as source on remote host')
    parser.add_argument('-u','--user', action='store', default=None, help='remote user')
    parser.add_argument('-t','--type', action='store', default=None, help='depending on \'type\' of directory, files and directories might be ignored. Currently known: git')

    parser.add_argument('-l','--log', action='store', default=None, help='logfile')
    parser.add_argument('-p','--pid', action='store', default=None, help='pid file')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-v', '--verbose', help="increase verbosity (show debugging messages)",
                       action='store_const', const=logging.DEBUG, dest='loglevel')
    

    args = parser.parse_args()
    
    if not args.log: 
        logging.basicConfig( format='%(asctime)-8s %(levelname)s:%(name)s: %(message)s', datefmt="%H:%M:%S", level=args.loglevel or logging.INFO )
    else:
         logging.basicConfig( format='%(asctime)-8s %(levelname)s:%(name)s: %(message)s', datefmt="%H:%M:%S", level=args.loglevel or logging.INFO, filename=args.log )

    logger = logging.getLogger('main')

    if not args.host and not args.dest:
        logger.error( 'you have to specify either remote host or destination directory !!! exiting...')
        sys.exit()

#    config = load_config()
#    jobs = create_jobs(config)
#    try:
#        while True:
#            sleep(1)
#    except KeyboardInterrupt:
#        observer.stop()
#        log.info("Normal shutdown")
#    observer.join()

    event_handler = LoggingEventHandler()
    observer = Observer()
    
    syncer = RsyncJob( observer, args )
    syncer.sync()
    observer.start()
    logger.info( 'watching ' + args.source + ' ...' )
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
