import abc
import logging

class DisableableBase(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, uid):
        self.uid = uid

    @abc.abstractmethod
    def entitlements(self):
        """Populate self.entitlement_list with self.uid's entitlements"""
        return

    @abc.abstractmethod
    def disable(self, entitlement):
        """Disable the entitlement."""
        return

class MrFakeDisable(DisableableBase):

    def entitlements(self):
        return ['superadmin', 'ninja', 'samurai']

    def disable(self, entitlement):
        logging.info("%s is no longer a %s", self.uid, entitlement)
        # always successful
        return True
