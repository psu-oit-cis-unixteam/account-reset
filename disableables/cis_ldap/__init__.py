from disableables import Disableable
from celery.task import task

@task(base=Disableable)
def get(uid):
    return ['wat']
