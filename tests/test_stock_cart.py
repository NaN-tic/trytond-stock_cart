# This file is part of the stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import doctest
import datetime
from decimal import Decimal
from dateutil.relativedelta import relativedelta
from functools import partial
from collections import defaultdict

import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.tests.test_tryton import doctest_setup, doctest_teardown
from trytond.tests.test_tryton import doctest_checker
from trytond.transaction import Transaction
from trytond.exceptions import UserWarning
from trytond.pool import Pool

from trytond.modules.company.tests import create_company, set_company


class StockCartTestCase(ModuleTestCase):
    'Test Stock Cart module'
    module = 'stock_cart'

    @with_transaction()
    def test0010picking(self):
        'Test Picking'

        pool = Pool()
        Company = pool.get('company.company')
        User = pool.get('res.user')
        Party = pool.get('party.party')
        Location = pool.get('stock.location')
        Move = pool.get('stock.move')
        Category = pool.get('product.category')
        Template = pool.get('product.template')
        Product = pool.get('product.product')
        Uom = pool.get('product.uom')
        Cart = pool.get('stock.cart')
        Sout_cart = pool.get('stock.shipment.out.cart')
        Sout_cart_line = pool.get('stock.shipment.out.cart.line')
        ShipmentOut = pool.get('stock.shipment.out')

        today = datetime.date.today()
        unit, = Uom.search([('name', '=', 'Unit')])
        supplier_loc, = Location.search([('code', '=', 'SUP')])
        customer_loc, = Location.search([('code', '=', 'CUS')])
        storage_loc, = Location.search([('code', '=', 'STO')])
        output_loc, = Location.search([('code', '=', 'OUT')])
        warehouse_loc, = Location.search([('code', '=', 'WH')])

        company = create_company()
        currency = company.currency

        # create customer
        customer, = Party.create([{
                    'name': 'Customer',
                    'addresses': [
                        ('create', [{
                            'street': 'St sample, 15',
                            }]),
                        ],
                    }])

        # create products
        template, = Template.create([{
                    'name': 'Product 1',
                    'type': 'goods',
                    'list_price': Decimal(1),
                    'cost_price': Decimal(0),
                    'cost_price_method': 'fixed',
                    'default_uom': unit.id,
                    }])
        product1, = Product.create([{
                    'template': template.id,
                    'code': 'PROD1',
                    }])
        template, = Template.create([{
                    'name': 'Product 2',
                    'type': 'goods',
                    'list_price': Decimal(1),
                    'cost_price': Decimal(0),
                    'cost_price_method': 'fixed',
                    'default_uom': unit.id,
                    }])
        product2, = Product.create([{
                    'template': template.id,
                    'code': 'PROD2',
                    }])
        template, = Template.create([{
                    'name': 'Product 3',
                    'type': 'goods',
                    'list_price': Decimal(1),
                    'cost_price': Decimal(0),
                    'cost_price_method': 'fixed',
                    'default_uom': unit.id,
                    }])
        product3, = Product.create([{
                    'template': template.id,
                    'code': 'PROD3',
                    }])

        with set_company(company):
            # create new locations
            loc1, loc2 = Location.create([{
                        'name': 'LOC1',
                        'type': 'storage',
                        'parent': storage_loc,
                        }, {
                        'name': 'LOC2',
                        'type': 'storage',
                        'parent': storage_loc,
                        }])
            loc1a, loc1b = Location.create([{
                        'name': 'LOC1A',
                        'type': 'storage',
                        'parent': loc1,
                        }, {
                        'name': 'LOC1B',
                        'type': 'storage',
                        'parent': loc1,
                        }])

            # create new cart
            cart, = Cart.create([{
                    'name': 'Cart1',
                    'rows': 2,
                    'columns': 2,
                    }])

            # upload user preferences
            User.write([User(Transaction().user)], {
                    'cart': cart.id,
                    'stock_warehouses': [
                        ('add', [warehouse_loc.id]),
                        ],
                    'stock_warehouse': warehouse_loc.id,
                    'stock_locations': [
                        ('add', [loc1.id]),
                        ],
                    })

            # create new inventory
            moves = Move.create([{
                        'product': product1,
                        'uom': unit.id,
                        'quantity': 10,
                        'from_location': supplier_loc.id,
                        'to_location': loc1.id,
                        'planned_date': today,
                        'effective_date': today,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        }, {
                        'product': product2,
                        'uom': unit.id,
                        'quantity': 10,
                        'from_location': supplier_loc.id,
                        'to_location': loc1a.id,
                        'planned_date': today,
                        'effective_date': today,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        }, {
                        'product': product3,
                        'uom': unit.id,
                        'quantity': 10,
                        'from_location': supplier_loc.id,
                        'to_location': loc2.id,
                        'planned_date': today,
                        'effective_date': today,
                        'company': company.id,
                        'unit_price': Decimal('1'),
                        'currency': currency.id,
                        }])
            Move.do([moves[0], moves[1], moves[2]])

            # create a shipment and moves with storage in loc1 locations
            shipment1, = ShipmentOut.create([{
                    'planned_date': today,
                    'customer': customer.id,
                    'delivery_address': customer.addresses[0].id,
                    'warehouse': warehouse_loc.id,
                    'company': company.id,
                    'outgoing_moves': [
                        ('create', [{
                            'product': product1.id,
                            'uom': unit.id,
                            'quantity': 2,
                            'from_location': output_loc.id,
                            'to_location': customer_loc.id,
                            'company': company.id,
                            'unit_price': Decimal('1'),
                            'currency': company.currency.id,
                            }, {
                            'product': product2.id,
                            'uom': unit.id,
                            'quantity': 2,
                            'from_location': output_loc.id,
                            'to_location': customer_loc.id,
                            'company': company.id,
                            'unit_price': Decimal('1'),
                            'currency': company.currency.id,
                            }]),
                        ],
                    }])

            # create a shipment and moves with storage in loc1 and loc2 locations
            shipment2, = ShipmentOut.create([{
                    'planned_date': today,
                    'customer': customer.id,
                    'delivery_address': customer.addresses[0].id,
                    'warehouse': warehouse_loc.id,
                    'company': company.id,
                    'outgoing_moves': [
                        ('create', [{
                            'product': product1.id,
                            'uom': unit.id,
                            'quantity': 2,
                            'from_location': output_loc.id,
                            'to_location': customer_loc.id,
                            'company': company.id,
                            'unit_price': Decimal('1'),
                            'currency': company.currency.id,
                            }, {
                            'product': product2.id,
                            'uom': unit.id,
                            'quantity': 2,
                            'from_location': output_loc.id,
                            'to_location': customer_loc.id,
                            'company': company.id,
                            'unit_price': Decimal('1'),
                            'currency': company.currency.id,
                            }, {
                            'product': product3.id,
                            'uom': unit.id,
                            'quantity': 2,
                            'from_location': output_loc.id,
                            'to_location': customer_loc.id,
                            'company': company.id,
                            'unit_price': Decimal('1'),
                            'currency': company.currency.id,
                            }]),
                        ],
                    }])

            # wait and assign try shipments
            ShipmentOut.wait([shipment1, shipment2])
            ShipmentOut.assign_try([shipment1, shipment2])

            # 1. Get products group by shipments
            products = Sout_cart.get_products()
            plocs = []
            for p in products:
                for k, v in p.iteritems():
                    plocs += v.get('locations')

            self.assertEqual(len(products), 2)
            self.assertEqual(products[0][1]['quantity'], 2.0)
            self.assertEqual(len(plocs), 2)

            # 2. Get products by cart
            sout_cart, = Sout_cart.create([{
                    'shipment': shipment2.id,
                    }])

            sout_carts = Sout_cart.search([])
            self.assertEqual(len(sout_carts), 2)
            products = Sout_cart.get_products_by_carts(sout_carts)
            self.assertEqual(len(products), 2)
            self.assertEqual(products[0][1]['quantity'], 4.0)

            # Picking lines
            pickings = {
                shipment1.number: {
                    'product': '1',
                    'qty': '2',
                    'location': 'LOC1',
                    },
                }
            Sout_cart_line.save_pickings(pickings)

            # Done carts
            Sout_cart.done(sout_carts)
            self.assertEqual(sout_cart.state, 'done')

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        StockCartTestCase))
    suite.addTests(doctest.DocFileSuite('scenario_stock_cart.rst',
            setUp=doctest_setup, tearDown=doctest_teardown, encoding='utf-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
