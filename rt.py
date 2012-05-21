"""A super minimal RT search client and parser for PSU Account reset requests"""

import logging
import requests

def get(query, credentials, url):
    """Query RT via the API.
    query: the RTQL query
    credentials: a username, password tuple
    url: base RT url"""
    query_string = {'query': query, 'orderby': '-Created', 'format': 's'}
    response = requests.post(url, data=credentials, params=query_string)
    if response.ok:
        return parse_search(response.text)
    else:
        raise Exception("RT Search Failed")

def parse_search(response):
    """Parse RT search results for account reset requests.
    response: an RT API response"""
    response = response.split('\n')
    status = response[0]
    # This is the RT request status, not HTTP status per se
    if '200' not in status:
        raise Exception("RT response parsing failed")
    # we skip the first and last lines in response as they're ''
    for req in response[2:-1]:
        # the ticket id is the first chunk before ': '
        ticket = req.split(': ')[0]
        # the account is the last word in req
        uid = req.split(' ')[-1]
        logging.debug('Yielding ticket=%s and user=%s', ticket, uid)
        yield (ticket, uid)
