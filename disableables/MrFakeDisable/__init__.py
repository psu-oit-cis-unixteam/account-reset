from disableables import Disableable
from celery.task import task
from random import choice
import logging

@task(base=Disableable)
def get(uid):
    return ['superadmin', 'ninja', 'samurai']
    
@task(base=Disableable)
def remove(uid, entitlement):
    """Disable an entitlement.
       Only sometimes be successful in the fake implementation.
    """
    # russian roulette failure
    win = choice([True, True, False])
    if not win:
        raise Exception("FAAAAAIL")
    else:
        return True
