from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cafe_send_to_kitchen = fields.Boolean(
        string='Send to Kitchen', help='Show this product on the kitchen queue even without a recipe.')
    cafe_recipe_ids = fields.One2many('cafe.recipe', 'product_tmpl_id', string='Recipes')
    cafe_recipe_count = fields.Integer(compute='_compute_cafe_recipe_count')

    def _compute_cafe_recipe_count(self):
        for rec in self:
            rec.cafe_recipe_count = len(rec.cafe_recipe_ids)

    def action_open_cafe_recipes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window', 'name': 'Recipes', 'res_model': 'cafe.recipe',
            'view_mode': 'tree,form', 'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }
