from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    cafe_in_kitchen = fields.Boolean(
        compute='_compute_cafe_in_kitchen',
        help='True when the product has a recipe or is flagged "Send to Kitchen". Loaded into the POS.')

    @api.depends('product_tmpl_id.cafe_send_to_kitchen', 'product_tmpl_id.cafe_recipe_ids')
    def _compute_cafe_in_kitchen(self):
        for prod in self:
            tmpl = prod.product_tmpl_id
            prod.cafe_in_kitchen = bool(tmpl.cafe_send_to_kitchen or tmpl.sudo().cafe_recipe_ids)
