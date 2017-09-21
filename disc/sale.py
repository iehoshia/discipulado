
#! -*- coding: utf8 -*-
# This file is part of the sale_pos module for Tryton.
# The COPYRIGHT file at the top level of this repository contains the full
# copyright notices and license terms.

from decimal import Decimal
from trytond.model import ModelView, fields, ModelSQL
from trytond.pool import PoolMeta, Pool
from trytond.pyson import Bool, Eval, Not
from trytond.transaction import Transaction
from trytond.wizard import Wizard, StateView, StateTransition, Button, StateAction
from trytond import backend
from trytond.tools import grouped_slice

__all__ = ['Sale', 'SaleWarehouse', 'ProductLine', 'WarehouseStock',
'WizardWarehouseStock']
__metaclass__ = PoolMeta
_ZERO = Decimal('0.0')

class Sale():
    'Sale'
    __name__ = 'sale.sale'

    @classmethod
    def __setup__(cls):
        super(Sale, cls).__setup__()
        cls._buttons.update({
                'warehouse_stock': {
                    'invisible': ((Eval('state') != 'draft') | (Eval('invoice_state') != 'none')),
                    },
                })
    @classmethod
    @ModelView.button_action('sale_stock_product_mini.warehouse_stock')
    def warehouse_stock(cls, sales):
        pass

class SaleWarehouse(ModelView, ModelSQL):
    'Producto por Bodega'
    __name__ = 'sale.warehouse'

    sale = fields.Many2One('sale.sale', 'Sale', readonly = True)
    product = fields.Char('Product',  readonly = True)
    warehouse = fields.Char('Warehouse',  readonly = True)
    quantity = fields.Char('Quantity', readonly = True)

class ProductLine(ModelView, ModelSQL):
    'Product Line'
    __name__ = 'product.product.line'

    sequence = fields.Integer('Sequence')
    product = fields.Many2One('product.product', 'Product')
    add = fields.Boolean('Add')
    quantity = fields.Numeric('Quantity')
    review = fields.Boolean('Verificar Stock')
    list_price = fields.Numeric('Precio Venta')
    total_stock = fields.Integer('Total Stock')

class WarehouseStock(ModelView):
    'Warehouse Stock'
    __name__ = 'sale_stock_product_mini.warehouse'
    product = fields.Char('Product')
    lines = fields.One2Many('product.product.line', None, 'Lines')
    warehouse_sale =fields.One2Many('sale.warehouse', 'sale', 'Product by Warehouse', readonly=True)

    @fields.depends('product', 'lines')
    def on_change_product(self):
        pool = Pool()
        Product = pool.get('product.product')
        Location = pool.get('stock.location')
        location = Location.search([('type', '=', 'warehouse')])
        Move = pool.get('stock.move')
        in_s = 0
        stock = 0
        s_total = 0
        stock_total = 0

        res = {}
        res['lines'] = {}
        if self.lines:
            res['lines']['remove'] = [x['id'] for x in self.lines]

        if not self.product:
            return res

        code = self.product+'%'
        name = self.product+'%'

        products = Product.search([('code', 'like', code)])
        if products:
            for product in products:
                stock_total = 0
                for lo in location:
                    in_stock = Move.search_count([('product', '=',  product), ('to_location','=', lo.storage_location)])
                    move = Move.search_count([('product', '=', product), ('from_location','=', lo.storage_location)])
                    s_total = in_stock - move
                    stock_total += s_total
                product_line = {
                    'product': product.id,
                    'total_stock':stock_total,
                }
                res['lines'].setdefault('add', []).append((0, product_line))
        else:
            products = Product.search([('name', 'ilike', name)])
            for product in products:
                stock_total = 0
                for lo in location:
                    in_stock = Move.search_count([('product', '=',  product), ('to_location','=', lo.storage_location)])
                    move = Move.search_count([('product', '=', product), ('from_location','=', lo.storage_location)])

                    s_total = in_stock - move
                    stock_total += s_total
                product_line = {
                    'product': product.id,
                    'total_stock':stock_total,
                }
                res['lines'].setdefault('add', []).append((0, product_line))

        return res


    @fields.depends('lines', 'warehouse_sale', 'product')
    def on_change_lines(self):
        pool = Pool()
        Location = pool.get('stock.location')
        location = Location.search([('type', '=', 'warehouse')])
        Move = pool.get('stock.move')
        stock = 0
        in_s = 0

        changes = {}
        changes['all_list_price'] = {}
        changes['warehouse_sale'] = {}
        changes['lines'] = {}

        if self.warehouse_sale:
            changes['warehouse_sale']['remove'] = [x['id'] for x in self.warehouse_sale]

        cont = 0
        if self.lines:
            for line in self.lines:
                cont += 1
                if line.review == True:
                    result_line = {
                        'review': False,
                        'product': line.product.id,
                        'list_price': line.list_price,
                        'total_stock': line.total_stock,
                        'add': line.add,
                        'quantity': line.quantity,
                    }
                    changes['lines']['remove'] = [line['id']]

                    changes['lines'].setdefault('add', []).append((cont-1, result_line))

                    for lo in location:
                        in_stock = Move.search_count([('product', '=',  line.product), ('to_location','=', lo.storage_location)])
                        move = Move.search_count([('product', '=', line.product), ('from_location','=', lo.storage_location)])

                        s_total = in_stock - move

                        result = {
                            'product': line.product.name,
                            'warehouse': lo.name,
                            'quantity': str(int(s_total)),
                        }
                        stock = 0
                        in_s = 0
                        changes['warehouse_sale'].setdefault('add', []).append((0, result))

        return changes

class WizardWarehouseStock(Wizard):
    'Wizard Warehouse Stock'
    __name__ = 'sale_stock_product_mini.warehouse_stock'

    start = StateView('sale_stock_product_mini.warehouse',
        'sale_stock_product_mini.warehouse_stock_view_form', [
            Button('Close', 'end', 'tryton-cancel'),
            Button('Add', 'add_', 'tryton-ok'),
        ])

    add_ = StateTransition()

    def transition_add_(self):
        return 'end'
