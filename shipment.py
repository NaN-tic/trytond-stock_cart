# This file is part of stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from json import dumps, loads
from logging import getLogger

from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval

__all__ = [
    'StockCart',
    'ShipmentOut',
    ]
__metaclass__ = PoolMeta


class StockCart(ModelSQL, ModelView):
    ' Stock Cart'
    __name__ = 'stock.cart'
    name = fields.Char('Name')
    rows = fields.Integer('Rows',
        help='Number of rows are available in this cart')
    columns = fields.Integer('Columns',
        help='Number of columns are available in this cart')
    active = fields.Boolean('Active')
    user = fields.Many2One('res.user', 'User',
        help='User who working in this cart')

    @staticmethod
    def default_active():
        return True

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

    def get_products(self, order):
        user = Transaction().user
        products = []
        products_to_cart = []
        shipment_grid = {}

        shipments = self.get_shipments()
        if not shipments:
            return products_to_cart, shipment_grid

        self.write(shipments, {'cart_shipment': True, 'cart_user': user})

        count = 0
        for shipment in shipments:
            count += 1
            grid_products = []
            grid_values = {}
            grid_values['name'] = shipment.name
            for move in shipment.move_lines:
                product = move.product
                ean13s = [c for c in product.codes if c.barcode == 'ean13']

                if ean13s:
                    ean13, = ean13s
                else:
                    ean13 = None
                    getLogger('stock_cart').info(
                        'Add an EAN13 on product ID %s.' % (product.id))

                locations = [p for p in product.locations]
                if locations:
                    location, = locations
                    product_location = '%s-%s-%s' % (
                            location.loc_rack,
                            location.loc_row,
                            location.loc_case,
                            )
                else:
                    location = None
                    product_location = None
                    getLogger('stock_cart').info(
                        'Add an location on product ID %s.' % (product.id))

                values = {
                    'id': product.id,
                    'product_name': product.name,
                    'product_code': product.code,
                    'product_ean13': ean13,
                    'product_qty_available': int(product.quantity),
                    'product_loc_rack': location.loc_rack if location else '',
                    'product_loc_row': location.loc_row if location else '',
                    'product_loc_case': location.loc_case if location else '',
                    'product_manufacturer': product.manufacturer.name or '',
                    'product_location': product_location,
                    'qty': int(move.quantity),
                    'shipment': move.shipment.id,
                    'shipment_name': move.shipment.name,
                    'location': move.from_location.name,
                    'move': move.id,
                    }
                products.append(values)
                grid_products.append(values)
            grid_values['products'] = grid_products
            shipment_grid[str(count)] = grid_values

        if not products:
            return products_to_cart, {}

        products_ordered = sorted(products, key=lambda k: k['id'])

        # Order by product
        qty = 0
        shipments = []
        count = 1
        total = len(products_ordered)

        for prod in products_ordered:
            product = prod.get('id')
            qty = qty + prod.get('qty')
            shipments.append({
                    'id': prod.get('shipment'),
                    'name': prod.get('shipment_name'),
                    'qty': prod.get('qty'),
                    'move': prod.get('move'),
                    })

            add = None
            if count != total:
                if product != products_ordered[count].get('id'):
                    add = True
            if count == total:
                add = True

            if add:
                products_to_cart.append({
                    'id': prod.get('id'),
                    'code': prod.get('product_code'),
                    'ean13': prod.get('product_ean13'),
                    'name': prod.get('product_name'),
                    'qty': qty,
                    'qty_available': prod.get('product_qty_available'),
                    'loc_rack': prod.get('product_loc_rack'),
                    'loc_row': prod.get('product_loc_row'),
                    'loc_case': prod.get('product_loc_case'),
                    'manufacturer': prod.get('product_manufacturer'),
                    'product_location': prod.get('product_location'),
                    'location': prod.get('location'),
                    'shipments': shipments,
                    })
                qty = 0
                shipments = []

            count = count + 1

        # Order
        if order:
            products_to_cart = sorted(products_to_cart, key=lambda k: k[order])

        return products_to_cart, shipment_grid


class ShipmentOut:
    __name__ = 'stock.shipment.out'
    stock_cart = fields.Boolean('Stock Cart',
        help='Shipment is processing in stock cart')
    cart = fields.Many2One('stock.cart', 'Cart',
        states={
            'invisible': ~Eval('stock_cart', True),
        },
        depends=['stock_cart'])
    cart_user = fields.Many2One('res.user', 'User',
        states={
            'invisible': ~Eval('stock_cart', True),
        },
        depends=['stock_cart'],
        help='User who made this shipment')
    cart_shipment = fields.Boolean('Picking',
        states={
            'invisible': ~Eval('stock_cart', True),
        },
        depends=['stock_cart'])

    @classmethod
    def __setup__(cls):
        super(ShipmentOut, cls).__setup__()
        cls._error_messages.update({
                'not_cart_selected':
                    'Select a cart to get shipments.',
                })

    @staticmethod
    def default_stock_cart():
        return True

    @classmethod
    def get_shipments_to_cart(cls, shipments):
        '''Return shipments to cart
        :param cart: object
        return list ids'''
        for shipment in shipments:
            if shipment.cart:
                return [p.id for p in shipment.cart.get_shipments()]

    @classmethod
    def get_products_to_cart(cls, cart, order=None):
        '''
        Get all shipments and assigned to a cart
        Return a list of products and their shipments
        :param cart int
        return list
        '''
        Cart = Pool.get('stock.cart')
        if not cart:
            cls.raise_user_error('not_cart_selected')
        cart = Cart(cart)
        return cart.get_products(order)

    @classmethod
    def set_products_to_cart(cls, cart, values):
        """
        Get all shipments and assigned to a cart
        Return a list of products and their shipments
        :param cart: int
        :param values: [{'shipment': 'ID', 'product': 'ID', 'qty': 1}]
        return True
        """
        StockMove = Pool().get('stock.move')
        user = Transaction().user
        shipments = []

        for value in values:
            if not value.get('move'):
                continue

            move = value.get('move')
            qty = value.get('qty')
            StockMove.write([move], {'received_quantity': qty})
            getLogger('stock_cart').info(
                'Update stock move %s qty %s' % (move, qty))

            move = StockMove.browse(move)
            shipments.append(move.shipment.id)

        shipments = [x for x in set(shipments)]
        cls.write(shipments, {
                'cart_shipment': False,
                'cart_id': cart,
                'cart_user': user,
                })
        getLogger('stock_cart').info(
            'End process shipments: %s.' % (shipments))
        return True

    @classmethod
    def stock_cart_print(cls, shipments, context=None):
        """
        Print shipments
        Overwrite this method to do print
        :param shipments: list shipment names
        return ids
        """
        ids = []
        for name in shipments:
            shipment = cls.search([('name', '=', name)])
            if not shipment:
                continue
            ids.append(shipment[0])

        getLogger('stock_cart').info(
            'Print shipments: %s.' % (shipments))
        return ids

    @classmethod
    def stock_cart_carrier(cls, shipments, context=None):
        """
        Carrier shipments
        Overwrite this method to delivery at carrier
        :param shipments: list shipment names
        return ids
        """
        ids = []
        for name in shipments:
            shipment = cls.search([('name', '=', name)])
            if not shipment:
                continue
            ids.append(shipment[0])

        getLogger('stock_cart').info(
            'Carrier shipments: %s.' % (shipments))
        return ids

    @classmethod
    def stock_cart_qty(cls, shipments):
        """
        Get qty from stock move
        :param shipments: JSON list shipment names
        return dict {'Picking number': {'move':'qty'}}
        """
        shipments = dumps(shipments)
        names = loads(shipments)

        ids = []
        for name in names:
            shipment = cls.search([('name', '=', name)])
            if not shipment:
                continue
            ids.append(shipment[0])

        result = {}
        for shipment in cls.browse(ids):
            moves = {}
            for move in shipment.move_lines:
                if not move.state == 'done':
                    moves[str(move.id)] = '--'
                else:
                    moves[str(move.id)] = str(int(move.quantity))
            result[shipment.name] = moves

        return result

    @classmethod
    def stock_cart_finish(cls, cart, shipments):
        """
        From shipments do extra methods
        Overwrite this method to do extra tasks
        :param cart: int
        :param shipments: list shipment names
        return ids
        """
        user = Transaction().user
        ids = []
        for name in shipments:
            shipment = cls.search([('name', '=', name)])
            if not shipment:
                continue
            ids.append(shipment[0])

        cls.write(ids, {
                'cart_shipment': False,
                'cart_id': cart,
                'cart_user': user,
                })
        getLogger('stock_cart').info(
            'End process shipments: %s.' % (shipments))
        return ids


class Move:
    __name__ = 'stock.move'

    @classmethod
    def __setup__(cls):
        super(Move, cls).__setup__()
        cls._error_messages.update({
                'split_exceeds_quantity':
                    'Total quantity after split exceeds the quantity to split '
                    'for this product: "%s" (id: %d)',
                })

    @classmethod
    def split_move(cls, move_ids, quantity):
        """
        Split stock move
        :param move_ids: list ID's stock move
        :param quantity: int qty
        return True
        """
        if quantity == 0:
            return True

        for move in cls.browse(move_ids):
            quantity_rest = move.quantity - quantity
            if quantity > move.quantity:
                cls.raise_user_error('split_exceeds_quantity',
                    error_args=(move.product.name, move.product.id,))
            if quantity > 0:
                cls.write([move.id], {
                    'product_qty': quantity,
                    'product_uos_qty': quantity,
                    'product_uos': move.product_uom.id,
                })

            if quantity_rest > 0 and quantity == 0.0:
                default_val = {
                    'product_qty': quantity_rest,
                    'product_uos_qty': quantity_rest,
                    'state': move.state,
                    'product_uos': move.product_uom.id
                }
                cls.copy([move.id], default_val)
        return True

    @classmethod
    def set_cart_to_move(cls, values):
        """
        Process stock move or split
        Return a list of products and their shipments
        :param values: {'name': 'ID stock move', 'value': 'qty'}
        return True
        """
        error = None
        for key, value in values.iteritems():
            move_id = int(key)
            qty = int(value)
            if qty == 0:
                continue

            move = cls.browse(move_id)
            move_qty = int(move.quantity)

            if move.state != 'assigned':
                getLogger('stock_cart').info(
                    'Move ID %s is not assigned.' % (move.id))
                error = True
                continue

            if not move_qty == qty:
                cls.split_move([move_id], qty)
            cls.action_done([move_id])  # done stock move

        if error:
            return False
        return True
