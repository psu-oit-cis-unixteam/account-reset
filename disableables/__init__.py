import logging

from celery.task import Task


class DisableableDebug(Task):
    abstract = True

    def after_return(self, *args, **kwargs):
        print("Returned: %r" % (self.request, ))
