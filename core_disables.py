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
        fake_entitlements = ['superadmin', 'ninja', 'samurai']
        logging.info('%s: uid=%s has entitlements="%s"', self.__class__.__name__, self.uid, str(fake_entitlements))
        return fake_entitlements

    def disable(self, entitlement):
        logging.info("%s is no longer a %s", self.uid, entitlement)
        # always successful in the fake implementation
        return True
