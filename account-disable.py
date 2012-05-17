#!/usr/bin/env python

from Queue import Queue
from threading import Thread

import rtResets
import sys
import logging
import yaml

def disabler():
    logging.debug('New disabler thread spawned.')
    while True:
        ticket, uid = account_resets.get()
        logging.info('Working on ticket=%s for uid=%s', ticket, uid)
        account_resets.task_done()

if __name__ == '__main__':
    with open('./config.yaml', 'r') as config_file:
        config = yaml.load(config_file)

    logging.basicConfig(
        format='[account-disable %(levelname)s] %(asctime)s: %(message)s',
        level=config['log_level'],
    )
    
    credentials = dict()
    credentials['user'] = config['rt_username']
    credentials['pass'] = config['rt_password']

    account_resets = Queue()
    for reset in rtResets.get(config['rt_query'], credentials, config['rt_search']):
        ticket, uid = reset
        account_resets.put(reset)
        logging.info('Added disable ticket=%s for uid=%s', ticket, uid)

    for i in range(config['worker_processes']):
        t = Thread(target=disabler)
        t.daemon = True
        t.start()
