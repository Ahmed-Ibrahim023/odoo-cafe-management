from odoo import fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    cafe_block_insufficient_stock = fields.Boolean(
        string='Block Sale When Ingredients Are Missing', default=True,
        help='The POS refuses to add a drink / validate an order when the recipe '
             'ingredients are not available in the POS stock location.')
