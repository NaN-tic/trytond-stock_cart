# This file is part of stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction

__all__ = ['StockCart']
__metaclass__ = PoolMeta


class StockCart(ModelSQL, ModelView):
    ' Stock Cart'
    __name__ = 'stock.cart'
    name = fields.Char('Name', required=True)
    rows = fields.Integer('Rows', required=True,
        help='Number of rows are available in this cart')
    columns = fields.Integer('Columns', required=True,
        help='Number of columns are available in this cart')
    active = fields.Boolean('Active')

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_rows():
        return 1

    @staticmethod
    def default_columns():
        return 1

    def get_shipments(self):
        Picking = Pool().get('stock.shipment.out')
        user = Transaction().user
        basket = self.rows * self.columns

        shipments = Picking.search([
                ('state', '=', 'assigned'),
                ('stock_cart', '=', True),
                ('cart_user', '=', user),
                ('cart_shipment', '=', True),
                ], limit=basket, order='planned_date asc')
        if shipments:
            return shipments

        shipments = Picking.search([
                ('state', '=', 'assigned'),
                ('stock_cart', '=', True),
                ('cart', '=', None),
                ('cart_shipment', '=', False),
                ], limit=basket, order='planned_date asc')
        return shipments
