#!/usr/bin/env python

from celeryconfig import get_implementations
import disableables
import rt

import imp
import logging
import yaml


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

    implementations = get_implementations('disableables', False)
    
    for module in implementations:
        f, filename, description = imp.find_module("{0}".format(module), disableables.__path__)
        vars()[module] = imp.load_module('disableables.{0}'.format(module), f, filename, description)

    # get reset requests from rt
    query, search = (config['rt_query'], config['rt_search'])
    for reset in rt.get(query, credentials, search):
        ticket, uid = reset
        logging.info('Working on ticket=%s for uid=%s', *reset)
        for module in implementations:
            instance = vars()[module]
            print instance.get.delay(uid)
