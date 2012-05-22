from disableables import Disableable
from celery.task.sets import subtask
from celery.task import task

CONFIG = ('ldap_server', 'ldap_basedn', 'ldap_cacert', 'username', 'password')

@task(base=Disableable)
def disable(ticket, uid, config):
    print "RT#{0}: disabling LDAP permissions for {1}".format(ticket, uid)
    get(uid, config=config, callback=subtask(remove))

@task(base=Disableable)
def get(uid, config, callback):
    return ['meowman']

@task(base=Disableable)
def remove(uid, config, callback):
    return True
