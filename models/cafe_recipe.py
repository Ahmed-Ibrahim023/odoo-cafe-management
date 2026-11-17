from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CafeRecipe(models.Model):
    _name = 'cafe.recipe'
    _description = 'Cafe Recipe'
    _inherit = ['mail.thread']
    _order = 'name'

    name = fields.Char(compute='_compute_name', store=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    product_tmpl_id = fields.Many2one('product.template', string='Product', required=True,
                                      ondelete='cascade', tracking=True)
    product_id = fields.Many2one(
        'product.product', string='Size / Variant', ondelete='cascade',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        help='Leave empty to use this recipe for every variant. '
             'Set it to give a specific size (Small / Medium / Large) its own recipe.')
    yield_qty = fields.Float(string='Recipe Yield', default=1.0,
                             help='Number of product units produced by the quantities below.')
    line_ids = fields.One2many('cafe.recipe.line', 'recipe_id', string='Ingredients', copy=True)
    note = fields.Text()
    currency_id = fields.Many2one(related='company_id.currency_id')
    cost = fields.Monetary(compute='_compute_cost', string='Cost / Unit')
    price = fields.Monetary(compute='_compute_cost', string='Sale Price')
    margin = fields.Monetary(compute='_compute_cost')
    margin_percent = fields.Float(compute='_compute_cost', string='Margin %')

    @api.depends('product_tmpl_id.name', 'product_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.product_id.display_name if rec.product_id else rec.product_tmpl_id.name

    @api.depends('line_ids.cost', 'yield_qty', 'product_id', 'product_tmpl_id.list_price')
    def _compute_cost(self):
        for rec in self:
            cost = sum(rec.line_ids.mapped('cost')) / (rec.yield_qty or 1.0)
            price = rec.product_id.lst_price if rec.product_id else rec.product_tmpl_id.list_price
            rec.cost = cost
            rec.price = price
            rec.margin = price - cost
            rec.margin_percent = (price - cost) / price * 100 if price else 0.0

    @api.constrains('yield_qty')
    def _check_yield(self):
        for rec in self:
            if rec.yield_qty <= 0:
                raise ValidationError(_('Recipe yield must be positive.'))

    @api.constrains('product_tmpl_id', 'product_id', 'company_id', 'active')
    def _check_unique(self):
        for rec in self.filtered('active'):
            dup = self.search_count([
                ('id', '!=', rec.id), ('product_tmpl_id', '=', rec.product_tmpl_id.id),
                ('product_id', '=', rec.product_id.id), ('company_id', '=', rec.company_id.id)])
            if dup:
                raise ValidationError(_('An active recipe already exists for %s.', rec.name))

    @api.model
    def _get_recipe_for(self, product, company=None):
        """Variant specific recipe wins over the template-wide one."""
        company = company or self.env.company
        recipes = self.sudo().search([
            ('product_tmpl_id', '=', product.product_tmpl_id.id),
            ('company_id', 'in', [False, company.id])])
        return (recipes.filtered(lambda r: r.product_id == product)[:1]
                or recipes.filtered(lambda r: not r.product_id)[:1])

    def _compute_requirements(self, qty):
        """Return {stock product.product: quantity in the product's stock UoM}
        needed to make `qty` units of the recipe's product."""
        self.ensure_one()
        factor = qty / (self.yield_qty or 1.0)
        needs = defaultdict(float)
        for line in self.line_ids:
            prod = line.ingredient_id.product_id
            needs[prod] += line.uom_id._compute_quantity(
                line.quantity * factor, prod.uom_id, round=False)
        return needs
