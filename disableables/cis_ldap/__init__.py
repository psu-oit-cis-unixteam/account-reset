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
    user_dn = "uid={0},ou=people,{1}".format(
                                             config['username'],
                                             config['ldap_basedn']
                                             )
    logging.info("Trying to bind as %s" % user_dn)
    try:
        # check the connection
        conn.simple_bind_s(user_dn, config['password'])
    except Exception:
        raise
    finally:
        return conn

@task(base=Disableable)
def disable(ticket, uid, config):
    print "RT#{0}: disabling LDAP permissions for {1}".format(ticket, uid)
    get.delay(uid, config=config, callback=subtask(remove))

@task(base=Disableable)
def get(uid, config, callback):
    conn = _setup(config)
    netgroups   =   conn.search_s(config['ldap_basedn'],
                                  ldap.SCOPE_SUBTREE,
                                  'nisnetgrouptriple=*,{},*'.format(uid),
                                  ['dn'])
    logging.info("%s is in netgroups='%s'", uid, str(netgroups))
    posixgroups =   conn.search_s(config['ldap_basedn'],
                                  ldap.SCOPE_SUBTREE,
                                  'memberuid={}'.format(uid),
                                  ['dn'])
    # every user has a group matching their username, it looks like this
    uid_group = ('cn={0},ou=Group,{1}'.format(uid, config['ldap_basedn']), {})
    try:
        # see if the user has a group with the same name as themself
        uid_group_index = posixgroups.index(uid_group)
    except ValueError:
        # woah funky
        logging.error("uid=%s lacks a their selfsame group=%s", uid, uid_group)
    else:
        # we do not want to remove this group, so ditch it from the list
        del posixgroups[uid_group_index]

    logging.info("%s has groups='%s'", uid, str(posixgroups))
    psupublish  =   conn.search_s(config['ldap_basedn'],
                                  ldap.SCOPE_SUBTREE,
                                  'uid={}'.format(uid),
                                  ['dn', 'psupublish'])
    conn.unbind()
    subtask(callback).delay(uid, config, (netgroups, posixgroups, psupublish))

@task(base=Disableable)
def remove(uid, config, items):
    netgroups, posixgroups, psupublish = items
    nistriple = "(-,{},-)".format(uid)
    for group in posixgroups:
        logging.info('Removing uid=%s from group=%s', uid, group)
    for group in netgroups:
        logging.info('Removing uid=%s from netgroup=%s', uid, group)
