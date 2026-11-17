import logging
from collections import defaultdict

from odoo import Command, _, api, fields, models
from odoo.tools import float_is_zero, float_round

_logger = logging.getLogger(__name__)


class PosOrderLine(models.Model):
    _inherit = 'pos.order.line'

    cafe_cost = fields.Float(string='Ingredient Cost', readonly=True, copy=False, digits='Product Price')
    cafe_profit = fields.Float(string='Gross Profit', compute='_compute_cafe_profit', store=True,
                               digits='Product Price')

    @api.depends('price_subtotal', 'cafe_cost')
    def _compute_cafe_profit(self):
        for line in self:
            line.cafe_profit = line.price_subtotal - line.cafe_cost


class PosOrder(models.Model):
    _inherit = 'pos.order'

    cafe_consumed = fields.Boolean(string='Ingredients Deducted', readonly=True, copy=False)
    cafe_error = fields.Text(string='Deduction Error', readonly=True, copy=False)
    cafe_move_ids = fields.One2many('stock.move', 'cafe_pos_order_id', string='Ingredient Moves', readonly=True)
    cafe_kitchen_order_id = fields.Many2one('cafe.kitchen.order', string='Kitchen Order',
                                            readonly=True, copy=False)
    cafe_cost = fields.Float(string='Ingredient Cost', compute='_compute_cafe_cost', store=True)
    cafe_profit = fields.Float(string='Gross Profit', compute='_compute_cafe_cost', store=True)

    @api.depends('lines.cafe_cost', 'lines.price_subtotal')
    def _compute_cafe_cost(self):
        for order in self:
            order.cafe_cost = sum(order.lines.mapped('cafe_cost'))
            order.cafe_profit = sum(order.lines.mapped('price_subtotal')) - order.cafe_cost

    # Hook: online AND offline-synced orders both end in action_pos_order_paid.
    def action_pos_order_paid(self):
        res = super().action_pos_order_paid()
        for order in self:
            order._cafe_process_paid_order()
        return res

    def _cafe_process_paid_order(self):
        """Never block a sale: failures are stored and retried by a cron / button."""
        self.ensure_one()
        order = self.sudo()
        if order.cafe_consumed:
            return  # duplicate confirmation -> nothing to do
        try:
            with self.env.cr.savepoint():
                order._cafe_create_kitchen_order()
                order._cafe_consume_ingredients()
                order.cafe_error = False
        except Exception as exc:  # noqa
            _logger.exception('Cafe ingredient deduction failed for %s', order.name)
            self.env.invalidate_all()
            order.cafe_error = str(exc)

    def _cafe_source_location(self):
        ptype = self.config_id.picking_type_id
        return ptype.default_location_src_id or ptype.warehouse_id.lot_stock_id

    def _cafe_create_kitchen_order(self):
        self.ensure_one()
        if self.cafe_kitchen_order_id:
            return
        Recipe = self.env['cafe.recipe']
        lines = []
        for line in self.lines.filtered(lambda l: l.qty > 0):
            if Recipe._get_recipe_for(line.product_id, self.company_id) \
                    or line.product_id.product_tmpl_id.cafe_send_to_kitchen:
                lines.append(Command.create({
                    'product_id': line.product_id.id, 'qty': line.qty,
                    'note': line.customer_note or '',
                }))
        if lines:
            self.cafe_kitchen_order_id = self.env['cafe.kitchen.order'].create({
                'pos_order_id': self.id, 'company_id': self.company_id.id, 'line_ids': lines})

    def _cafe_consume_ingredients(self):
        self.ensure_one()
        if self.cafe_consumed:
            return
        Recipe = self.env['cafe.recipe']
        restock = self.env['ir.config_parameter'].sudo().get_param(
            'cafe_management.restock_on_refund') in ('True', 'true', '1')

        needs = defaultdict(float)
        for line in self.lines:
            recipe = Recipe._get_recipe_for(line.product_id, self.company_id)
            if not recipe:
                continue
            line.cafe_cost = recipe.cost * line.qty  # negative on refunds -> profit reverses too
            for product, qty in recipe._compute_requirements(line.qty).items():
                needs[product] += qty

        src = self._cafe_source_location()
        moves = self.env['stock.move']
        for product, qty in needs.items():
            if float_is_zero(qty, precision_rounding=product.uom_id.rounding):
                continue
            prod_loc = product.with_company(self.company_id).property_stock_production
            if qty > 0:
                from_loc, to_loc = src, prod_loc
            elif restock:           # refund + company chose to put ingredients back
                from_loc, to_loc, qty = prod_loc, src, -qty
            else:                   # refunded drink was already made -> no stock back
                continue
            moves |= self.env['stock.move'].create({
                'name': _('Cafe: %s', self.name), 'origin': self.name,
                'product_id': product.id, 'product_uom': product.uom_id.id,
                'product_uom_qty': qty, 'location_id': from_loc.id,
                'location_dest_id': to_loc.id, 'company_id': self.company_id.id,
                'cafe_pos_order_id': self.id,
            })
        if moves:
            moves._action_confirm()
            moves._action_assign()
            for move in moves:
                move.quantity_done = move.product_uom_qty
            moves._action_done()
        self.cafe_consumed = True

    def action_cafe_retry(self):
        for order in self.filtered(lambda o: not o.cafe_consumed and o.state in ('paid', 'done', 'invoiced')):
            order._cafe_process_paid_order()

    @api.model
    def _cron_cafe_retry_failed(self):
        self.search([('cafe_consumed', '=', False), ('cafe_error', '!=', False)]).action_cafe_retry()

    @api.model
    def cafe_check_availability(self, config_id, lines):
        """Called by the POS screen before adding a drink / validating an order.

        :param lines: [{'product_id': int, 'qty': float}, ...] (whole order)
        :return: {'ok': bool, 'shortages': [{'name', 'needed', 'available', 'uom'}]}
        """
        config = self.env['pos.config'].sudo().browse(config_id)
        if not config.exists() or not config.cafe_block_insufficient_stock:
            return {'ok': True, 'shortages': []}
        Recipe = self.env['cafe.recipe']
        needs = defaultdict(float)
        for line in lines:
            qty = line.get('qty') or 0.0
            if qty <= 0:      # refunds never need ingredients
                continue
            product = self.env['product.product'].sudo().browse(line['product_id'])
            recipe = Recipe._get_recipe_for(product, config.company_id)
            if recipe:
                for prod, needed in recipe._compute_requirements(qty).items():
                    needs[prod] += needed
        ptype = config.picking_type_id
        location = ptype.default_location_src_id or ptype.warehouse_id.lot_stock_id
        Quant = self.env['stock.quant'].sudo()
        shortages = []
        for prod, needed in needs.items():
            available = Quant._get_available_quantity(prod, location)
            rounding = prod.uom_id.rounding
            if float_round(available - needed, precision_rounding=rounding) < 0:
                ingredient = self.env['cafe.ingredient'].sudo().search([('product_id', '=', prod.id)], limit=1)
                shortages.append({
                    'name': ingredient.name or prod.display_name,
                    'needed': float_round(needed, precision_rounding=rounding),
                    'available': float_round(max(available, 0.0), precision_rounding=rounding),
                    'uom': prod.uom_id.name,
                })
        return {'ok': not shortages, 'shortages': shortages}
