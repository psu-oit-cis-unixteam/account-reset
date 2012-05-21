import logging

from celery.task import Task

class Disableable(Task):
    abstract = True

    def after_return(self, *args, **kwargs):
        print("Returned: %r" % (self.request, ))
