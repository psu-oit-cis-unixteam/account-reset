#!/usr/bin/env python

from Queue import Queue
from threading import Thread

import core_disables
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
    
    # use introspection to load disableable implementations
    disableables = [subclass.__name__ for subclass in core_disables.DisableableBase.__subclasses__()]
    logging.info('Loaded disableables: %s', ' '.join(disableables))
    
    credentials = dict()
    credentials['user'] = config['rt_username']
    credentials['pass'] = config['rt_password']

    account_resets = Queue()
    for reset in rtResets.get(config['rt_query'], credentials, config['rt_search']):
        ticket, uid = reset
        logging.debug('Examining reset ticket=%s for uid=%s', ticket, uid)
        for disableable in disableables:
            a_disableable = getattr(core_disables, disableable)
            instance = a_disableable(uid)
            logging.info('Inspecting entitlements for uid=%s, disableable=%s, ticket=%s', uid, disableable, ticket)
            instance.entitlements()
        account_resets.put(reset)

    for i in range(config['worker_processes']):
        t = Thread(target=disabler)
        t.daemon = True
        t.start()
