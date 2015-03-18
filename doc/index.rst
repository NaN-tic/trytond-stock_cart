Stock Cart Module
#################

Packing shipments (out) in warehouse using carts.

- Define carts and how many baskets (rows * columns).
- Current cart  user is working in user preferences.

Methods RPC
-----------

Get Products
------------

Return dict with:

* Product ID
* Name
* Code
* Shipments: {id, code, qty}
* Carts

This method lock table because not assign same shipments in other carts/users.

Default values:

* Warehouse: None
* State: Assigned
* Total Attempts: 5

Done Cart
---------

Change cart state to done.
