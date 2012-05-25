"""A super minimal RT search client and parser for PSU Account reset requests"""

import logging
import requests

def get(query, credentials, url):
    """Query RT via the API.
    query: the RTQL query
    credentials: a username, password tuple
    url: base RT url"""
    url = "{}/search/ticket".format(url)
    query_string = {'query': query, 'orderby': '-Created', 'format': 's'}
    response = requests.post(url, data=credentials, params=query_string)
    if response.ok:
        return parse_search(response.text)
    else:
        raise Exception("RT: Search Failed")

def parse_search(response):
    """Parse RT search results for account reset requests.
    response: an RT API response"""
    message = split_response(response)
    for req in message:
        # the ticket id is the first chunk before ': '
        ticket = req.split(': ')[0]
        # the account is the last word in req
        uid = req.split(' ')[-1]
        logging.debug('RT: Yielding ticket=%s and user=%s', ticket, uid)
        yield (ticket, uid)

def split_response(rt_response):
    """RT sends it's own 'status' in addition to content.
       This function returns a tuple of status and message"""
    response = rt_response.split('\n')
    # This is the RT request status, not HTTP status per se
    if '200 Ok' in response[0]:
        # we skip the first and last lines in response as they're ''
        message = response[2:-1]        # it may be possible to do [2:-2] here
        logging.info("RT: response='%s'", message)
        return message
    else:
        raise Exception("RT: response indicates failure...")


def comment(ticket, comment, credentials, url):
    """Post a comment to a ticket at the url
       ticket: ticket id
       comment: comment text
       credentials: a user, pass dict
       url: base RT url"""
    url += "/ticket/{}/comment".format(ticket)
    content = "id: {0}\nAction: comment\nText: {1}".format(ticket, comment)
    post_data = credentials
    post_data['content'] = content
    response = requests.post(url, data=post_data)
    message = split_response(response.text)
    if 'Message recorded' in message[0]:
        return True
    else:
        return False

def edit(ticket, values, credentials, url):
    url += "/ticket/{}/edit".format(ticket)
    post_data = credentials
    edits = list()
    for key in values.iterkeys():
        edits.append("{0}: {1}".format(key, values[key]))
    post_data['content'] = "\n".join(edits)
    response = requests.post(url, data=post_data)
    message = split_response(response.text)
    if 'updated' in message[0]:
        return True
    else:
        return False

def move(ticket, queue, credentials, url, unown=True):
    values = {"Queue": queue}
    if unown:
        values['Owner'] = "Nobody"
    return edit(ticket, values, credentials, url)
