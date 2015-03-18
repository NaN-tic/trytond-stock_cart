# This file is part of stock_cart module for Tryton.
# The COPYRIGHT file at the top level of this repository contains
# the full copyright notices and license terms.
from trytond.model import ModelView, ModelSQL, fields
from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.pyson import Eval, Equal, Not
from trytond.rpc import RPC

import logging

__all__ = ['StockCart', 'StockShipmentOutCart']
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


class StockShipmentOutCart(ModelSQL, ModelView):
    ' Stock Shipment Cart'
    __name__ = 'stock.shipment.out.cart'
    shipment = fields.Many2One('stock.shipment.out', 'Shipment', required=True,
        states={
            'readonly': Not(Equal(Eval('state'), 'draft')),
        }, depends=['state'])
    cart = fields.Many2One('stock.cart', 'Cart', required=True,
        states={
            'readonly': Not(Equal(Eval('state'), 'draft')),
        }, depends=['state'])
    user = fields.Many2One('res.user', 'User', required=True,
        states={
            'readonly': Not(Equal(Eval('state'), 'draft')),
        }, depends=['state'])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ], 'State', readonly=True)

    @classmethod
    def __setup__(cls):
        super(StockShipmentOutCart, cls).__setup__()
        cls._sql_constraints += [
            ('shipment_uniq', 'UNIQUE(shipment)',
                'The shipment must be unique!'),
            ]
        cls._order.insert(0, ('shipment', 'DESC'))
        cls._error_messages.update({
            'shipment_uniq': 'The shipment must be unique!',
            })
        cls._buttons.update({
            'done': {
                'invisible': Eval('state') == 'done',
                },
            'draft': {
                'invisible': Eval('state') == 'draft',
                },
            })
        cls.__rpc__.update({
            'get_shipments': RPC(readonly=False),
            })

    @staticmethod
    def default_state():
        return 'draft'

    @staticmethod
    def default_cart():
        User = Pool().get('res.user')
        user = User(Transaction().user)
        return user.cart.id if user.cart else None

    @staticmethod
    def default_user():
        return Transaction().user

    @classmethod
    @ModelView.button
    def done(cls, carts):
        cls.write(carts, {
            'state': 'done',
            })

    @classmethod
    @ModelView.button
    def draft(cls, carts):
        cls.write(carts, {
            'state': 'draft',
            })

    @classmethod
    def get_shipments(cls, warehouse=None, state=['assigned'], attempts=0, total_attempts=5):
        '''
        Return a list shipments
        @param warehouse: ID warehouse domain to search shipments
        @param state: list. Shipment states to filter
        @param attempts: int. Attempts when table is lock
        @param total_attempts: int. Total attempts to try get shipments unlock
        '''
        pool = Pool()
        Shipment = pool.get('stock.shipment.out')
        Carts = pool.get('stock.shipment.out.cart')
        User = pool.get('res.user')

        transaction = Transaction()
        user = User(Transaction().user)

        if not user.cart:
            logging.getLogger('Stock Cart').warning(
                'User %s not have cart in their preferences' % user.rec_name)
            return []
        baskets = user.cart.rows * user.cart.columns

        domain = [('state', 'in', state)]
        if warehouse:
            domain.append(('warehouse', '=', warehouse))

        try:
            # Locks transaction. Nobody can query this table
            transaction.cursor.lock(Carts._table)
        except:
            # Table is locked. Captures operational error and returns void list
            if attempts < total_attempts:
                cls.get_shipments(state, attempts+1, total_attempts)
            else:
                logging.getLogger('Stock Cart').warning(
                    'Table Carts is lock after %s attempts' % (total_attempts))
                return []
        else:
            # if there are carts state draft, return first this carts
            carts = Carts.search_read([
                ('state', '=', 'draft'),
                ('user', '=', user),
                ], limit=baskets)
            if carts:
                return carts

            # Assign new shipments
            shipments = [s.id for s in Shipment.search(domain, order=[('planned_date', 'ASC')])]

            carts_assigned = [c.shipment.id for c in Carts.search([
                ('shipment', 'in', shipments),
                ])]

            #TODO. Respect order shipments
            shipments_cart = list(set(shipments) - set(carts_assigned))

            # Save carts assigned to user
            to_create = []
            for s in shipments_cart[:baskets]:
                to_create.append({'shipment': s})
            if to_create:
                carts = Carts.create(to_create)
                return carts
        return []
