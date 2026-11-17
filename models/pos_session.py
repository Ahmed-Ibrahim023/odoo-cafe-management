from odoo import models


class PosSession(models.Model):
    _inherit = 'pos.session'

    def _loader_params_product_product(self):
        res = super()._loader_params_product_product()
        fields = res['search_params']['fields']
        if fields:  # empty list = "load all fields", never turn it into a restriction
            fields.append('cafe_in_kitchen')
        return res

    def _loader_params_pos_config(self):
        res = super()._loader_params_pos_config()
        # In Odoo 17 pos.config is loaded with fields=[] (= ALL fields).
        # Appending to an empty list would restrict the read to our field only,
        # so only extend explicit lists.
        fields = res['search_params']['fields']
        if fields:
            fields.append('cafe_block_insufficient_stock')
        return res
