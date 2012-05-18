from disableables import DisableableBase
import logging

class MrFakeDisable(DisableableBase):

    def entitlements(self):
        fake_entitlements = ['superadmin', 'ninja', 'samurai']
        logging.info('%s: uid=%s has entitlements="%s"', self.__class__.__name__, self.uid, str(fake_entitlements))
        return fake_entitlements

    def disable(self, entitlement):
        logging.info("%s is no longer a %s", self.uid, entitlement)
        # always successful in the fake implementation
        return True
