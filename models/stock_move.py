from odoo import fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    cafe_pos_order_id = fields.Many2one('pos.order', string='Cafe POS Order', index=True,
                                        copy=False, readonly=True)
    cafe_waste_id = fields.Many2one('cafe.waste', string='Cafe Waste', index=True,
                                    copy=False, readonly=True)
