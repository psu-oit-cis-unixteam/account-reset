import logging
import requests

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
