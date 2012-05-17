#!/usr/bin/env python

from Queue import Queue
from threading import Thread

import requests
import sys
import logging
import yaml

def get_resets(query, credentials, url):
        q = {'query': query, 'orderby': '-Created', 'format': 's'}
        rs = requests.post(url, data=credentials, params=q)
        if rs.ok:
            return parse_search(rs.text)
        else:
            raise Exception("RT Search Failed")

def parse_search(response):
    r = response.split('\n')
    status = r[0]
    if '200' not in status:
        raise Exception("RT response parsing failed")
    # we skip the first and last lines in r as they're ''
    for req in r[2:-1]:
        # the ticket id is the first chunk before ': '
        ticket = req.split(': ')[0]
        # the account is the last word in req
        uid = req.split(' ')[-1]
        logging.debug('Yielding ticket=%s and user=%s', ticket, uid)
        yield (ticket, uid)

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
    for reset in get_resets(config['rt_query'], credentials, config['rt_search']):
        ticket, uid = reset
        account_resets.put(reset)
        logging.info('Added disable ticket=%s for uid=%s', ticket, uid)

    for i in range(config['worker_processes']):
        t = Thread(target=disabler)
        t.daemon = True
        t.start()
