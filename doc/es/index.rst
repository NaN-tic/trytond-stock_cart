========================================
Albaranes de salida en carros de almacén
========================================

Gestión de albaranes de salida para ser procesados mediante carros en el almacén
para ser procesados en global.

Una vez se obtiene los albaranes reservados, el mozo de almacén realiza la búsqueda
de los productos para después empaquetar cada producto en un albarán.

La gestión en Tryton simplemente se realiza:

* Definición de carritos y compartimientos de este.
* Asignación de albarán de salida con el carrito y el compartimiento.

La gestión de búsqueda de productos en el almacén se realiza con un Apps en una tablet
que consulta la información de Tryton.

Logística. Packing mediante carritos
####################################

Gestión de albaranes de salida para ser procesados mediante carros en el almacén.

* Definición de carritos y compartimientos de este.
* Preferencias usuario el carrito en que esta trabajando

Métodos RPC
-----------

Get Products
------------

Devuelve un diccionario con:

 - Product ID
 - Name
 - Code
 - Shipments: {id, code, qty}
 - Carts

Este método bloquea la tabla para no se asignen otros albaranes en otros carritos/usuarios.

Valores por defecto:

 - Warehouse: None
 - State: Assigned
 - Total Attempts: 5

Done Cart
---------

Cambia de estado el carrito de borrador a realizado.
