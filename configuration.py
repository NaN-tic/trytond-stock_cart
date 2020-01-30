# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
from trytond.model import fields
from trytond.pool import PoolMeta

__all__ = ['Configuration']


class Configuration:
    __name__ = 'stock.configuration'
    __metaclass__ = PoolMeta
    stock_cart_create_issue = fields.Boolean('Create Issue')

    @staticmethod
    def default_stock_cart_create_issue():
        return False
