#!/usr/bin/env python
""" Load the disableable implementations then enqueue disabling activities."""

from celeryconfig import get_implementations
import disableables
import rt

from imp import find_module, load_module
from time import sleep
import logging
import yaml
    
IMPLEMENTATIONS = get_implementations('disableables', False)

def main():
    """Load a config, load modules, get tasks from RT dispatch disable tasks
       for each of them."""
    with open('./config.yaml', 'r') as config_file:
        config = yaml.load(config_file)

    logging.basicConfig(
        format='[account-disable %(levelname)s] %(asctime)s: %(message)s',
        level=config['log_level'],
    )
    
    credentials = dict()
    credentials['user'] = config['rt_username']
    credentials['pass'] = config['rt_password']

    for module in IMPLEMENTATIONS:
        parent = "disableables.{0}".format(module)
        fhn, filename, description = find_module(module, disableables.__path__)
        vars()[module] = load_module(parent, fhn, filename, description)

    # get reset requests from rt
    query, search = (config['rt_query'], config['rt_search'])
    for reset in rt.get(query, credentials, search):
        ticket, uid = reset
        logging.info('Working on ticket=%s for uid=%s', ticket, uid)
        tasks = dict()
        for module in IMPLEMENTATIONS:
            instance = vars()[module]
            instance_config = dict()
            for key in instance.CONFIG:
                instance_config[key] = config[key]
            task = instance.disable.delay(ticket, uid, config)
            tasks[ticket] = (uid, task)
            print "RT#{0}: {1} is {2}".format(ticket, uid, task.status)
        while True:
            if len(tasks) < 1: break
            done = list()
            for ticket in tasks.iterkeys():
                uid, task = tasks[ticket]
                if task.status == "SUCCESS":
                    print "RT#{0}: {1} is {2}".format(ticket, uid, task.status)
                    done.append(ticket)
            # can't delete dict items during iteration, causes runtime error
            for ticket in done:
                del tasks[ticket]

if __name__ == '__main__':
    main()
