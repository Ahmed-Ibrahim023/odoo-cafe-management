from odoo import _, api, fields, models


class CafeIngredient(models.Model):
    _name = 'cafe.ingredient'
    _description = 'Cafe Ingredient'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    product_id = fields.Many2one(
        'product.product', string='Stock Product', required=True, ondelete='restrict',
        domain="[('detailed_type', '=', 'product')]",
        help='Storable product that holds the real stock of this ingredient.')
    uom_id = fields.Many2one(related='product_id.uom_id', string='Stock UoM', readonly=True)
    standard_price = fields.Float(related='product_id.standard_price', string='Cost / Stock UoM',
                                  readonly=True, digits='Product Price')
    qty_available = fields.Float(compute='_compute_qty_available', string='On Hand',
                                 digits='Product Unit of Measure')
    min_qty = fields.Float(string='Minimum Quantity', digits='Product Unit of Measure',
                           help='A reminder is created when on-hand stock falls to this level.')
    is_low_stock = fields.Boolean(compute='_compute_qty_available')

    _sql_constraints = [
        ('product_uniq', 'unique(product_id)', 'This stock product is already used by another ingredient.'),
    ]

    @api.depends('product_id', 'min_qty')
    def _compute_qty_available(self):
        for rec in self:
            rec.qty_available = rec.product_id.qty_available
            rec.is_low_stock = bool(rec.min_qty) and rec.qty_available <= rec.min_qty

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id and not self.name:
            self.name = self.product_id.name

    @api.model
    def _cron_low_stock_alert(self):
        """Schedule one to-do per low ingredient for storekeepers/managers."""
        group = self.env.ref('cafe_management.group_cafe_storekeeper')
        users = group.users.filtered(lambda u: u.active and u.id != 1) or self.env.ref('base.user_admin')
        for ing in self.search([('min_qty', '>', 0)]):
            if ing.qty_available > ing.min_qty:
                continue
            summary = _('Low stock: %s', ing.name)
            if ing.activity_ids.filtered(lambda a: a.summary == summary):
                continue
            ing.activity_schedule(
                'mail.mail_activity_data_todo', summary=summary,
                note=_('On hand: %(qty)s %(uom)s (minimum %(min)s).',
                       qty=ing.qty_available, uom=ing.uom_id.name, min=ing.min_qty),
                user_id=users[0].id)
