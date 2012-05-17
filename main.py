#!/usr/bin/env python

from threading import Thread
import yaml
import requests
import sys
from Queue import Queue

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
        account = req.split(' ')[-1]
        yield (ticket, account)

def disabler():
    while True:
        ticket, uid = account_resets.get()
        print "Ticket: {}\nUser: {}\n".format(ticket, uid)
        account_resets.task_done()

if __name__ == '__main__':
    with open('./config.yaml', 'r') as config_file:
        config = yaml.load(config_file)
    
    credentials = dict()
    credentials['user'] = config['rt_username']
    credentials['pass'] = config['rt_password']

    account_resets = Queue()
    for reset in get_resets(config['rt_query'], credentials, config['rt_search']):
        account_resets.put(reset)

    for i in range(config['worker_processes']):
        t = Thread(target=disabler)
        t.daemon = True
        t.start()
