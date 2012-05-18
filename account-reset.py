#!/usr/bin/env python

from pkgutil import iter_modules as pkg_iter
from Queue import Queue
from threading import Thread

import disableables

import rt_util
import imp
import logging
import os.path
import yaml

# get the path of the disableables module directory
_, disableable_path, _ = imp.find_module('disableables')
# enumerate the modules in the disableables directory
implementations = [name for _, name, _ in pkg_iter([disableable_path])]
# This is equivelant to: from disableables.MrFakeDisable import MrFakeDisable
for module in implementations:
    f, filename, description = imp.find_module(module, disableables.__path__)
    pp = imp.load_module("{0}.{0}".format(module), f, filename, description)
    vars()[module] = getattr(pp, module)

def disabler():
    logging.debug('New disabler thread spawned.')
    while True:
        task = account_resets.get()
        log_args = (task['ticket'], task['uid'])
        logging.info('Working on ticket=%s for uid=%s', *log_args)
        instance = task['disableable']
        # get the user's entitlements for this implementation
        entitlements = instance.entitlements()
        log_args = (task['implementation'], task['uid'], entitlements)
        logging.info('%s: uid=%s has entitlements="%s"', *log_args)
            
        for entitlement in entitlements:
            log_args = (task['implementation'], task['uid'], entitlement)
            try:
                instance.disable(entitlement)
            except Exception as err:
                log_args = (task['implementation'], task['uid'], entitlement, err)
                logging.error('%s: uid=%s entitlement=%s not disabled, error: %s',
                              *log_args)
            else:
                logging.info('%s: uid=%s lost entitlement=%s', *log_args)
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
    query, search = (config['rt_query'], config['rt_search'])
    for reset in rt_util.get(query, credentials, search):
        task = dict()
        task['ticket'], task['uid'] = reset
        for implementation in implementations:
            a_disableable = vars()[implementation]
            task['implementation'] = implementation
            try:
                # try to instantiate our disableable
                task['disableable'] = a_disableable(task['uid'])
            except TypeError as err:
                # happens if the implementation doesn't comply with the ABC
                logging.error(err)
            else:
                account_resets.put(task)

    account_resets.join()
