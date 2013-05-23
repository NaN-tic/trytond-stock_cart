# This file is part of stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.pool import Pool
from .shipment import *


def register():
    Pool.register(
        StockCart,
        ShipmentOut,
        module='stock_cart', type_='model')
