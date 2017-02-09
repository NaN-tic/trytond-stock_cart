===================
Stock Cart Scenario
===================

"""
- Create shipments out and assigned
- Create shipment carts with assigned shipments
- Create an inventory
- Done shipments carts
"""

Imports::

    >>> import datetime
    >>> from dateutil.relativedelta import relativedelta
    >>> from decimal import Decimal
    >>> from proteus import config, Model, Wizard
    >>> from trytond.modules.company.tests.tools import create_company, \
    ...     get_company
    >>> today = datetime.date.today()

Create database::

    >>> config = config.set_trytond()
    >>> config.pool.test = True

Install stock Module::

    >>> Module = Model.get('ir.module')
    >>> stock_module, = Module.find([('name', '=', 'stock_cart')])
    >>> stock_module.click('install')
    >>> Wizard('ir.module.install_upgrade').execute('upgrade')

Create company::

    >>> _ = create_company()
    >>> company = get_company()

Reload the context::

    >>> User = Model.get('res.user')
    >>> config._context = User.get_preferences(True, config.context)

Create customer::

    >>> Party = Model.get('party.party')
    >>> customer = Party(name='Customer')
    >>> customer.save()

Get stock locations::

    >>> Location = Model.get('stock.location')
    >>> warehouse_loc, = Location.find([('code', '=', 'WH')])
    >>> supplier_loc, = Location.find([('code', '=', 'SUP')])
    >>> storage_loc, = Location.find([('code', '=', 'STO')])
    >>> customer_loc, = Location.find([('code', '=', 'CUS')])
    >>> output_loc, = Location.find([('code', '=', 'OUT')])

Create products::

    >>> ProductUom = Model.get('product.uom')
    >>> ProductTemplate = Model.get('product.template')
    >>> unit, = ProductUom.find([('name', '=', 'Unit')])

    >>> template1 = ProductTemplate()
    >>> template1.name = 'Product 1'
    >>> template1.default_uom = unit
    >>> template1.type = 'goods'
    >>> template1.list_price = Decimal('10')
    >>> template1.cost_price = Decimal('5')
    >>> template1.save()
    >>> product1, = template1.products

    >>> template2 = ProductTemplate()
    >>> template2.name = 'Product 2'
    >>> template2.default_uom = unit
    >>> template2.type = 'goods'
    >>> template2.list_price = Decimal('20')
    >>> template2.cost_price = Decimal('10')
    >>> template2.save()
    >>> product2, = template2.products

Fill storage::

    >>> StockMove = Model.get('stock.move')
    >>> incoming_move = StockMove()
    >>> incoming_move.product = product1
    >>> incoming_move.uom = unit
    >>> incoming_move.quantity = 10
    >>> incoming_move.from_location = supplier_loc
    >>> incoming_move.to_location = storage_loc
    >>> incoming_move.planned_date = today
    >>> incoming_move.effective_date = today
    >>> incoming_move.company = company
    >>> incoming_move.unit_price = Decimal('10')
    >>> incoming_move.currency = company.currency
    >>> incoming_moves = [incoming_move]

    >>> incoming_move = StockMove()
    >>> incoming_move.product = product2
    >>> incoming_move.uom = unit
    >>> incoming_move.quantity = 10
    >>> incoming_move.from_location = supplier_loc
    >>> incoming_move.to_location = storage_loc
    >>> incoming_move.planned_date = today
    >>> incoming_move.effective_date = today
    >>> incoming_move.company = company
    >>> incoming_move.unit_price = Decimal('15')
    >>> incoming_move.currency = company.currency
    >>> incoming_moves.append(incoming_move)
    >>> StockMove.click(incoming_moves, 'do')

Create carts:

    >>> Cart = Model.get('stock.cart')
    >>> cart = Cart()
    >>> cart.name = 'Cart1'
    >>> cart.rows = 2
    >>> cart.columns = 2
    >>> cart.save()

Assign cart to user:

    >>> user, = User.find([], limit=1)
    >>> user.cart = cart
    >>> user.save()
    >>> config._context = User.get_preferences(True, config.context)

Create Shipment Out and assign::

    >>> ShipmentOut = Model.get('stock.shipment.out')
    >>> shipment_out = ShipmentOut()
    >>> shipment_out.planned_date = today
    >>> shipment_out.customer = customer
    >>> shipment_out.warehouse = warehouse_loc
    >>> shipment_out.company = company
    >>> move1 = StockMove()
    >>> shipment_out.outgoing_moves.append(move1)
    >>> move1.product = product1
    >>> move1.uom =unit
    >>> move1.quantity = 2
    >>> move1.from_location = output_loc
    >>> move1.to_location = customer_loc
    >>> move1.company = company
    >>> move1.unit_price = Decimal('1')
    >>> move1.currency = company.currency
    >>> move2 = StockMove()
    >>> shipment_out.outgoing_moves.append(move2)
    >>> move2.product = product2
    >>> move2.uom =unit
    >>> move2.quantity = 1
    >>> move2.from_location = output_loc
    >>> move2.to_location = customer_loc
    >>> move2.company = company
    >>> move2.unit_price = Decimal('1')
    >>> move2.currency = company.currency
    >>> shipment_out.save()

    >>> shipment_out.click('wait')
    >>> shipment_out.reload()
    >>> shipment_out.click('assign_try')
    True
    >>> shipment_out.reload()

Do picking::

    >>> ShipmentOutCart = Model.get('stock.shipment.out.cart')
    >>> ShipmentOutCartLine = Model.get('stock.shipment.out.cart.line')

    >>> scart = ShipmentOutCart()
    >>> scart.shipment = shipment_out
    >>> scart.cart = cart
    >>> scart.user = user
    >>> scart.save()

    >>> scartline = ShipmentOutCartLine()
    >>> scartline.shipment = shipment_out
    >>> scartline.from_location = storage_loc
    >>> scartline.cart = cart
    >>> scartline.user = user
    >>> scartline.product = product1
    >>> scartline.quantity = 2
    >>> scartline.save()

Create inventory::

    >>> Inventory = Model.get('stock.inventory')
    >>> inventory = Inventory()
    >>> inventory.location = storage_loc
    >>> inventory.save()
    >>> inventory.click('complete_lines')
    >>> inventory.reload()
    >>> len(inventory.lines)
    2
    >>> inventory.lines[0].picking_quantity
    2.0
    >>> inventory.lines[1].picking_quantity
    0.0
