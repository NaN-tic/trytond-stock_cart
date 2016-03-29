# This file is part stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['User']


class User:
    __metaclass__ = PoolMeta
    __name__ = "res.user"
    cart = fields.Many2One('stock.cart', 'Cart')

    @classmethod
    def __setup__(cls):
        super(User, cls).__setup__()
        cls._preferences_fields.extend([
                'cart',
                ])
        cls._context_fields.insert(0, 'cart')

    def get_status_bar(self, name):
        status = super(User, self).get_status_bar(name)
        if self.cart:
            status += ' - %s' % (self.cart.rec_name)
        return status
