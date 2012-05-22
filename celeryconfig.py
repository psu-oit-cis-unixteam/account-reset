""" Connect to a local AMQP broker as guest and dynamically load disableable
    implementations. """

from pkgutil import iter_modules as pkg_iter

import imp
import logging

def get_implementations(parent_package, fullname=True):
    """Enumerate the modules in parent_package"""
    _, path, _ = imp.find_module(parent_package)
    implementations = list()
    for _, name, _ in pkg_iter([path]):
        if fullname:
            implementations.append("{0}.{1}".format(parent_package, name))
        else:
            implementations.append("{0}".format(name))
    logging.debug('Loaded disableables: %s', " ".join(implementations))
    return tuple(implementations)

BROKER_URL = "amqp://guest@127.0.0.1:5672//"
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = get_implementations('disableables')
