# This file is part of stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from . import cart
from . import inventory
from . import user


def register():
    Pool.register(
        cart.StockCart,
        cart.StockShipmentOutCart,
        cart.StockShipmentOutCartLine,
        inventory.Inventory,
        inventory.InventoryLine,
        user.User,
        module='stock_cart', type_='model')
