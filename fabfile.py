from fabric.api import *
import ldap
import rt
import yaml
import logging

@task
def clean():
    '''get rid of compiled python elements'''
    local('find . -name "*.pyc" -exec rm -rf {} \;')

@task
def lint():
    '''lint python'''
    local('find . -name "*.py" | xargs pylint | tee pylint.log | less')

def _config(config='./config.yaml'):
    '''import config file'''
    with open(config, 'r') as config_file:
        return yaml.load(config_file)

#add config file as global
CONF=_config()

def _ldap_setup():
    '''setup an ldap connection from the current conf.'''
    conn = ldap.initialize(CONF['ldap_server'])
    conn.protocol_version=ldap.VERSION3
    conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
    conn.set_option(ldap.OPT_X_TLS_CACERTFILE, CONF['ldap_cacert'])
    conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
    username = "uid={0},ou=people,{1}".format(
            CONF['username'],
            CONF['ldap_basedn'])
    logging.info("Trying to bind as %s" % username)

    try:
        # check the connection
        conn.simple_bind_s(username, CONF['password'])
    except Exception:
        raise
    finally:
        return conn

@task
def do_resets():
    '''gets a list of requests and then fab.execute's each item from the
    returned list.'''
    requests = get_requests()
    for reset in requests:
        ticket, uid = reset
        print "RT#{0}: resetting {1}".format(ticket, uid)
        execute(reset_ldap, uid)

@task
def get_requests():
    '''uses credentials from the current conf to query rt for acct reset
    ticks. returns list of ticks.'''
    credentials = dict()
    credentials['user'] = CONF['rt_username']
    credentials['pass'] = CONF['rt_password']
    return rt.get(CONF['rt_query'], credentials, CONF['rt_search'])

@task
def reset_ldap(uid):
    '''takes uid as parameter. gets lists of netgroups and posixgroups user
    belongs to. deletes selfname group from list of posix groups. gets 
    psupublish. fab-executes remove.'''
    conn = _ldap_setup()
    netgroups = conn.search_s(
        CONF['ldap_basedn'],
        ldap.SCOPE_SUBTREE,
        'nisnetgrouptriple=*,{},*'.format(uid),
        ['dn'])
    logging.info("%s is in netgroups='%s'", uid, str(netgroups))
    posixgroups = conn.search_s(
        CONF['ldap_basedn'],
        ldap.SCOPE_SUBTREE,
        'memberuid={}'.format(uid),
        ['dn'])
    # every user has a group matching their username, it looks like this
    uid_group = ('cn={0},ou=Group,{1}'.format(uid, CONF['ldap_basedn']), {})
    try:
        #see if the user has a group with the same name as themself
        uid_group_index = posixgroups.index(uid_group)
    except ValueError:
        logging.error("uid=%s lacks a selfsame group=%s", uid, uid_group)
    else:
        #we do not want to remove this group, so ditch it from the list
        del posixgroups[uid_group_index]

    logging.info("%s has groups'%s'",uid,str(posixgroups))
    psupublish = conn.search_s(
            CONF['ldap_basedn'],
            ldap.SCOPE_SUBTREE,
            'uid={}'.format(uid),
            ['psupublish'])
    logging.info("psupublish=%s for uid=%s", str(psupublish[0]), uid)

    conn_unbind()
    #fabric.execute for the remove operation. take the user out of each netgroup, posixgroup
    #reset psupublish.
    return execute(remove, (uid, config, (netgroups, posixgroups, psupublish[0])))

@task
def remove(uid, config, items):
    '''remove sets up the mods dict so that the acct perms can be reset.'''
    netgroups, posixgroups, (userdn, psupublish) = items
    nistriple = "(-,{},-)".format(uid)
    memberuid = "memberuid={}".format(uid)
    mods = dict()
    for group in posixgroups:
        dn, _ = group
        mods[dn] = (ldap.MOD_DELETE, 'memberUid', memberuid)
        logging.debug('removing of uid=%s from group=%s', uid, dn)
    for dn in netgroups:
        mods[dn] = (ldap.MOD_DELETE, 'nisNetgroupTriple', nistriple)
        logging.debug('Queueing removal of uid=%s from netgroup=%s', uid, dn)
    mods[userdn] = (ldap.MOD_REPLACE, 'psuPublish', 'no')
    logging.info('Modifications for uid=%s is modlist=%s', uid, str(mods))
    #always true for debug
    return True
