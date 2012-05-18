#!/usr/bin/env python

from Queue import Queue
from threading import Thread

import disableables

import rt_util
import sys
import logging
import os.path
import pkgutil
import yaml

## CRAZY DYNAMIC MODULE LOADING GOING ON RIGHT HERE
def _load_module(module, package):
    """Load a module programmatically."""
    package_name = "{}.{}".format(package, module)
    _temp = __import__(package_name, fromlist=[module])
    return getattr(_temp, module)

# get the path of the disableables module directory
disableable_path = os.path.dirname(disableables.__file__)
# enumerate the modules in the disableables directory
implementations = [name for _, name, _ in pkgutil.iter_modules([disableable_path])]
# This is equivelant to: from disableables.MrFakeDisable import MrFakeDisable
for module in implementations:
    vars()[module] = _load_module(module, 'disableables')
##

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
    
    #implemented_disableables = implementations
    logging.info('Loaded disableables: %s', ' '.join(implementations))
    
    credentials = dict()
    credentials['user'] = config['rt_username']
    credentials['pass'] = config['rt_password']

    # set up the reset queue
    account_resets = Queue()

    # start the workers
    logging.debug('Spawning %s workers.', config['worker_processes'])
    for i in range(config['worker_processes']):
        t = Thread(target=disabler)
        t.daemon = True
        t.start()

    # get reset requests from rt
    for reset in rt_util.get(config['rt_query'], credentials, config['rt_search']):
        ticket, uid = reset
        logging.debug('Examining reset ticket=%s for uid=%s', ticket, uid)
        for implementation in implementations:
            a_disableable = vars()[implementation]
            try:
                # try to instantiate our disableable
                instance = a_disableable(uid)
            except TypeError as err:
                # this will happen if the implementation doesn't comply with the ABC
                logging.error(err)
            logging.info('Inspecting entitlements for uid=%s, disableable=%s, ticket=%s', uid, implementation, ticket)
            instance.entitlements()
        account_resets.put(reset)

