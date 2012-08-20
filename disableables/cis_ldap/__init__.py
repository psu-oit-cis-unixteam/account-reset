if __name__ == '__main__':
    class task(object):
        """A neutered implementation of celeryd's @task"""
        def __init__(self, f, *args, **kwargs):
            """f is the callable, the rest is any args at invokation"""
            self.f = f
            self.args = args
            self.kwargs = kwargs

        def __call__(self, *args, **kwargs):
            """actually call f() on the args"""
            self.f(*args, **kwargs)
            #TODO: log args
            logging.debug("Running fake task decorator around: %s", f)

        def delay(self, *args, **kwargs):
            """If we haven't had args for f() before, set and return self."""
            self.args = args
            self.kwargs = kwargs
            return self

        def get(self):
            """actually call"""
            self.__call__(self, *self.args, **self.kwargs)

    class subtask(task):
        """In this simplification, this is identical to task()"""
        pass

else:
    from celery.task.sets import subtask
    from celery.task import task

import ldap
import logging

# configuration details this task will need from dispatch
CONFIG = ('ldap_server', 'ldap_basedn', 'ldap_cacert', 'username', 'password')

def _setup(config):
    conn = ldap.initialize(config['ldap_server'])
    conn.protocol_version = ldap.VERSION3
    conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
    conn.set_option(ldap.OPT_X_TLS_CACERTFILE, config['ldap_cacert'])
    conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
    user_dn = "uid={0},ou=people,{1}".format(
                                             config['username'],
                                             config['ldap_basedn']
                                             )
    logging.info("Trying to bind as %s", user_dn)
    try:
        # check the connection
        conn.simple_bind_s(user_dn, config['password'])
    except Exception:
        raise
    finally:
        return conn

@task
def disable(ticket, uid, config):
    print "RT#{0}: disabling LDAP permissions for {1}".format(ticket, uid)
    return get_ent.delay(uid, config=config, callback=subtask(remove)).get()

@task
def get_ent(uid, config, callback):
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
        logging.error("uid=%s lacks a group=%s", uid, uid_group)
    else:
        # we do not want to remove this group, so ditch it from the list
        del posixgroups[uid_group_index]

    logging.info("%s has groups='%s'", uid, str(posixgroups))
    psupublish  =   conn.search_s(config['ldap_basedn'],
                                  ldap.SCOPE_SUBTREE,
                                  'uid={}'.format(uid),
                                  ['psupublish'])
    logging.info("psupublish=%s for uid=%s", str(psupublish[0]), uid)
    conn.unbind()
    return subtask(callback).delay(uid, config, (netgroups, posixgroups,
                                                 psupublish[0]))

@task
def remove(uid, config, items):
    netgroups, posixgroups, (userdn, psupublish) = items
    nistriple = "(-,{},-)".format(uid)
    memberuid = "memberuid={}".format(uid)
    mods = dict()
    for group in posixgroups:
        dn, _ = group
        mods[dn] = (ldap.MOD_DELETE, 'memberUid', memberuid)
        logging.debug('Queueing removal of uid=%s from group=%s', uid, dn)
    for dn in netgroups:
        mods[dn] = (ldap.MOD_DELETE, 'nisNetgroupTriple', nistriple)
        logging.debug('Queueing removal of uid=%s from netgroup=%s', uid, dn)
    mods[userdn] = (ldap.MOD_REPLACE,  'psuPublish', 'no')
    logging.info('Modifications for uid=%s is modlist=%s', uid, str(mods))
    success = list()
    for dn in mods.iterkeys():
        try:
            ldap.modify_s(dn, [mods[dn]])
        except Exception:
            logging.error('Failed to modify dn={0} with mods={1!r}'.format(dn, mods[dn]))
        else:
            successes.append('Modified dn={0} with mods={1!r}'.format(dn, mods[dn]))
    if len(success) > 0:
        return "\n".join(successes)

if __name__ == '__main__':
    #TODO: load and use the config
    disable("12345", "meow", "emwo")
