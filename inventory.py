# This file is part of stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import fields
from trytond.pool import Pool, PoolMeta
from trytond.pyson import Eval

__all__ = ['InventoryLine']


class InventoryLine:
    __metaclass__ = PoolMeta
    __name__ = 'stock.inventory.line'
    picking_quantity = fields.Float('Picking Quantity',
        digits=(16, Eval('unit_digits', 2)), depends=['unit_digits'])

    @staticmethod
    def default_picking_quantity():
        return 0

    @fields.depends('product', 'inventory')
    def on_change_product(self):
        CartLine = Pool().get('stock.shipment.out.cart.line')

        super(InventoryLine, self).on_change_product()

        if self.product:
            picking_quantity = 0
            for line in CartLine.search([
                    ('product', '=', self.product),
                    ('from_location', '=', self.inventory.location),
                    ('shipment.state', '=', 'assigned')
                    ]):
                picking_quantity += line.quantity
            self.picking_quantity = picking_quantity
