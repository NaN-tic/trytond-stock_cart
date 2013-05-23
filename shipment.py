# This file is part of stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import PoolMeta

__all__ = [
    'StockCart',
    'ShipmentOut',
    ]
__metaclass__ = PoolMeta


class StockCart(ModelSQL, ModelView):
    ' Stock Cart'
    __name__ = 'stock.cart'
    name = fields.Char('Name')
    basket = fields.Integer("Basket")
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True


class ShipmentOut:
    __name__ = 'stock.shipment.out'
    cart = fields.Many2One('stock.cart', 'Cart')
    basket = fields.Integer("Basket")
