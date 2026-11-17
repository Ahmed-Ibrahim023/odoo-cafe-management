from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CafeRecipeLine(models.Model):
    _name = 'cafe.recipe.line'
    _description = 'Cafe Recipe Line'

    recipe_id = fields.Many2one('cafe.recipe', required=True, ondelete='cascade')
    ingredient_id = fields.Many2one('cafe.ingredient', required=True, ondelete='restrict')
    quantity = fields.Float(digits='Product Unit of Measure', default=1.0, required=True)
    uom_category_id = fields.Many2one(related='ingredient_id.product_id.uom_id.category_id')
    uom_id = fields.Many2one(
        'uom.uom', string='Unit', required=True, compute='_compute_uom_id',
        store=True, readonly=False, precompute=True,
        domain="[('category_id', '=', uom_category_id)]")
    cost = fields.Float(compute='_compute_cost', digits='Product Price')

    @api.depends('ingredient_id')
    def _compute_uom_id(self):
        for line in self:
            if line.ingredient_id and (not line.uom_id or line.uom_id.category_id != line.uom_category_id):
                line.uom_id = line.ingredient_id.product_id.uom_id

    @api.depends('quantity', 'uom_id', 'ingredient_id.standard_price')
    def _compute_cost(self):
        for line in self:
            prod = line.ingredient_id.product_id
            if prod and line.uom_id:
                qty = line.uom_id._compute_quantity(line.quantity, prod.uom_id, round=False)
                line.cost = qty * prod.standard_price
            else:
                line.cost = 0.0

    @api.constrains('quantity', 'uom_id', 'ingredient_id')
    def _check_line(self):
        for line in self:
            if line.quantity <= 0:
                raise ValidationError(_('Ingredient quantity must be positive.'))
            if line.uom_id.category_id != line.ingredient_id.product_id.uom_id.category_id:
                raise ValidationError(_('Unit "%(u)s" is not compatible with ingredient "%(i)s".',
                                        u=line.uom_id.name, i=line.ingredient_id.name))
