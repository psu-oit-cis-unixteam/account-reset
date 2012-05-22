from disableables import Disableable
from celery.task.sets import subtask
from celery.task import task

import ldap
import logging

# configuration details this task will need from dispatch
CONFIG = ('ldap_server', 'ldap_basedn', 'ldap_cacert', 'username', 'password')

def _setup(config):
    conn = ldap.initialize(config['ldap_server'])
    conn.protocol_version=ldap.VERSION3
    conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
    conn.set_option(ldap.OPT_X_TLS_CACERTFILE, config['ldap_cacert'])
    conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
    try:
        # check the connection
        conn.simple_bind_s(config['username'], config['password'])
    except Exception:
        raise
    finally:
        return conn

@task(base=Disableable)
def disable(ticket, uid, config):
    print "RT#{0}: disabling LDAP permissions for {1}".format(ticket, uid)
    get(uid, config=config, callback=subtask(remove))

@task(base=Disableable)
def get(uid, config, callback):
    conn = _setup(config)
    print "NETGROUPS: {}".format(conn.search_s("dc=pdx,dc=edu", ldap.SCOPE_SUBTREE, 'nisnetgrouptriple=*,{},*'.format(uid), ['dn']))
    print conn.search_s("dc=pdx,dc=edu", ldap.SCOPE_SUBTREE, 'uid={}'.format(uid), ['dn', 'maillocaladdress'])
    conn.unbind()
    return ''

@task(base=Disableable)
def remove(uid, config, callback):
    return True
