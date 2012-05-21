from pkgutil import iter_modules as pkg_iter

import imp
import logging

def get_implementations(parent_module, fullname=True):
    _, path, _ = imp.find_module(parent_module)
    if fullname:
        implementations = ["{0}.{1}".format(parent_module, name) for _, name, _ in pkg_iter([path])]
    else:
        implementations = ["{0}".format(name) for _, name, _ in pkg_iter([path])]
    logging.debug('Loaded disableables: %s', " ".join(implementations))
    return tuple(implementations)

BROKER_URL = "amqp://guest@127.0.0.1:5672//"
CELERY_RESULT_BACKEND = "amqp"
CELERY_IMPORTS = get_implementations('disableables')
