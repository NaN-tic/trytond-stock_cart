# This file is part of the stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.
import unittest
import doctest
import datetime
from decimal import Decimal
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase
from trytond.tests.test_tryton import POOL, DB_NAME, USER, CONTEXT
from trytond.tests.test_tryton import doctest_setup, doctest_teardown
from trytond.transaction import Transaction


class StockCartTestCase(ModuleTestCase):
    'Test Stock Cart module'
    module = 'stock_cart'

    def setUp(self):
        super(StockCartTestCase, self).setUp()
        self.company = POOL.get('company.company')
        self.user = POOL.get('res.user')
        self.party = POOL.get('party.party')
        self.location = POOL.get('stock.location')
        self.move = POOL.get('stock.move')
        self.category = POOL.get('product.category')
        self.template = POOL.get('product.template')
        self.product = POOL.get('product.product')
        self.uom = POOL.get('product.uom')
        self.cart = POOL.get('stock.cart')
        self.sout_cart = POOL.get('stock.shipment.out.cart')
        self.sout_cart_line = POOL.get('stock.shipment.out.cart.line')
        self.shipment_out = POOL.get('stock.shipment.out')

    def test0010picking(self):
        'Test Picking'
        with Transaction().start(DB_NAME, USER, context=CONTEXT):
            today = datetime.date.today()
            unit, = self.uom.search([('name', '=', 'Unit')])
            supplier_loc, = self.location.search([('code', '=', 'SUP')])
            customer_loc, = self.location.search([('code', '=', 'CUS')])
            storage_loc, = self.location.search([('code', '=', 'STO')])
            output_loc, = self.location.search([('code', '=', 'OUT')])
            warehouse_loc, = self.location.search([('code', '=', 'WH')])

            company, = self.company.search([
                    ('rec_name', '=', 'Dunder Mifflin'),
                    ])
            currency = company.currency

            self.user.write([self.user(USER)], {
                'main_company': company.id,
                'company': company.id,
                })

            # create customer
            customer, = self.party.create([{
                        'name': 'Customer',
                        'addresses': [
                            ('create', [{
                                'street': 'St sample, 15',
                                }]),
                            ],
                        }])

            # create products
            category, = self.category.create([{
                        'name': 'Test Picking',
                        }])
            template, = self.template.create([{
                        'name': 'Product 1',
                        'type': 'goods',
                        'list_price': Decimal(1),
                        'cost_price': Decimal(0),
                        'category': category.id,
                        'cost_price_method': 'fixed',
                        'default_uom': unit.id,
                        }])
            product1, = self.product.create([{
                        'template': template.id,
                        'code': 'PROD1',
                        }])
            template, = self.template.create([{
                        'name': 'Product 2',
                        'type': 'goods',
                        'list_price': Decimal(1),
                        'cost_price': Decimal(0),
                        'category': category.id,
                        'cost_price_method': 'fixed',
                        'default_uom': unit.id,
                        }])
            product2, = self.product.create([{
                        'template': template.id,
                        'code': 'PROD2',
                        }])
            template, = self.template.create([{
                        'name': 'Product 3',
                        'type': 'goods',
                        'list_price': Decimal(1),
                        'cost_price': Decimal(0),
                        'category': category.id,
                        'cost_price_method': 'fixed',
                        'default_uom': unit.id,
                        }])
            product3, = self.product.create([{
                        'template': template.id,
                        'code': 'PROD3',
                        }])

            # create new locations
            loc1, loc2 = self.location.create([{
                        'name': 'LOC1',
                        'type': 'storage',
                        'parent': storage_loc,
                        }, {
                        'name': 'LOC2',
                        'type': 'storage',
                        'parent': storage_loc,
                        }])
            loc1a, loc1b = self.location.create([{
                        'name': 'LOC1A',
                        'type': 'storage',
                        'parent': loc1,
                        }, {
                        'name': 'LOC1B',
                        'type': 'storage',
                        'parent': loc1,
                        }])

            # create new cart
            cart, = self.cart.create([{
                    'name': 'Cart1',
                    'rows': 2,
                    'columns': 2,
                    }])

            # upload user preferences
            self.user.write([self.user(USER)], {
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
            moves = self.move.create([{
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
            self.move.do([moves[0], moves[1], moves[2]])

            # create a shipment and moves with storage in loc1 locations
            shipment1, = self.shipment_out.create([{
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
            shipment2, = self.shipment_out.create([{
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
            self.shipment_out.wait([shipment1, shipment2])
            self.shipment_out.assign_try([shipment1, shipment2])

            # 1. Get products group by shipments
            products = self.sout_cart.get_products()
            plocs = []
            for p in products:
                for k, v in p.iteritems():
                    plocs += v.get('locations')

            self.assertEqual(len(products), 2)
            self.assertEqual(products[0][1]['quantity'], 2.0)
            self.assertEqual(len(plocs), 2)

            # 2. Get products by cart
            sout_cart, = self.sout_cart.create([{
                    'shipment': shipment2.id,
                    }])

            sout_carts = self.sout_cart.search([])
            self.assertEqual(len(sout_carts), 2)
            products = self.sout_cart.get_products_by_carts(sout_carts)
            self.assertEqual(len(products), 2)
            self.assertEqual(products[0][1]['quantity'], 4.0)

            # Picking lines
            pickings = {
                shipment1.code: {
                    'product': '1',
                    'qty': '2',
                    'location': 'LOC1',
                    },
                }
            self.sout_cart_line.save_pickings(pickings)

            # Done carts
            self.sout_cart.done(sout_carts)
            self.assertEqual(sout_cart.state, 'done')

def suite():
    suite = trytond.tests.test_tryton.suite()
    from trytond.modules.company.tests import test_company
    for test in test_company.suite():
        if test not in suite and not isinstance(test, doctest.DocTestCase):
            suite.addTest(test)
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        StockCartTestCase))
    suite.addTests(doctest.DocFileSuite('scenario_stock_cart.rst',
            setUp=doctest_setup, tearDown=doctest_teardown, encoding='utf-8',
            optionflags=doctest.REPORT_ONLY_FIRST_FAILURE))
    return suite
