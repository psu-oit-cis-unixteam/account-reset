from disableables import DisableableBase
from random import choice
import logging

class MrFakeDisable(DisableableBase):

    def entitlements(self):
        self.entitlements = ['superadmin', 'ninja', 'samurai']
        return self.entitlements

    def disable(self, entitlement):
        """Disable an entitlement.
           Only sometimes be successful in the fake implementation.
        """
        # russian roulette failure
        return choice([True, True, False, False, False])
