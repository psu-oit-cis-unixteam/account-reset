from disableables import DisableableBase
import logging

class MrFakeDisable(DisableableBase):

    def entitlements(self):
        self.entitlements = ['superadmin', 'ninja', 'samurai']
        return self.entitlements

    def disable(self, entitlement):
        # always successful in the fake implementation
        return True
