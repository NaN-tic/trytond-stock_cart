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
    rows = fields.Integer('Rows', help='Number of rows are available in this cart')
    columns = fields.Integer('Columns', help='Number of columns are available in this cart')
    active = fields.Boolean('Active')
    user = fields.Many2One('res.user', 'User', help='User who working in this cart')

    @staticmethod
    def default_active():
        return True


class ShipmentOut:
    __name__ = 'stock.shipment.out'
    cart = fields.Many2One('stock.cart', 'Cart')
    cart_user = fields.Many2One('res.user', 'User', help='User who made this picking')
    cart_picking = fields.Boolean('Picking')
