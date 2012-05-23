from fabric.api import *
import ldap
import rt
import yaml

@task
def clean():
    local('find . -name "*.pyc" -exec rm -rf {} \;')

@task
def lint():
    local('find . -name "*.py" | xargs pylint | tee pylint.log | less')

def _config(config='./config.yaml'):
    with open(config, 'r') as config_file:
        return yaml.load(config_file)

CONF=_config()

def _ldap_setup():
    conn = ldap.initialize(CONF['ldap_server'])
    conn.protocol_version=ldap.VERSION3
    conn.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_DEMAND)
    conn.set_option(ldap.OPT_X_TLS_CACERTFILE, CONF['ldap_cacert'])
    conn.set_option(ldap.OPT_X_TLS_NEWCTX, 0)
    username = "uid={},ou=people,dc=pdx,dc=edu".format(CONF['username'])
    try:
        conn.simple_bind_s(username, CONF['password'])
    except Exception:
        raise
    finally:
        return conn

@task
def do_resets():
    requests = get_requests()
    for reset in requests:
        ticket, uid = reset
        print "RT#{0}: resetting {1}".format(*reset)
        execute(reset_ldap, uid)

@task
def get_requests():
    credentials = dict()
    credentials['user'] = CONF['rt_username']
    credentials['pass'] = CONF['rt_password']
    return rt.get(CONF['rt_query'], credentials, CONF['rt_search'])

@task
def reset_ldap(uid):
    conn = _ldap_setup()
    ng = conn.search_s(CONF['ldap_basedn'], ldap.SCOPE_SUBTREE, 'nisnetgrouptriple=*,{},*'.format(uid), ['dn'])
    pg = conn.search_s(CONF['ldap_basedn'], ldap.SCOPE_SUBTREE, 'memberuid={}'.format(uid), ['dn'])
    publish = conn.search_s(CONF['ldap_basedn'], ldap.SCOPE_SUBTREE, 'uid={}'.format(uid), ['dn', 'psupublish'])
    print "\t{0}\n\t{1}\n\t{2}".format(ng,pg,publish)
    conn.unbind()
