from odoo import _, api, fields, models
from odoo.exceptions import UserError


class CafeKitchenOrder(models.Model):
    _name = 'cafe.kitchen.order'
    _description = 'Cafe Kitchen Order'
    _inherit = ['mail.thread']
    _order = 'date_received desc, id desc'

    name = fields.Char(default='/', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    pos_order_id = fields.Many2one('pos.order', string='POS Order', ondelete='cascade', index=True, readonly=True)
    pos_reference = fields.Char(related='pos_order_id.pos_reference', string='Receipt Ref.', store=True)
    config_id = fields.Many2one(related='pos_order_id.config_id', store=True, string='Point of Sale')
    kitchen_ticket = fields.Char(compute='_compute_kitchen_ticket', store=True,
                                 help='Short number shown on the POS receipt and the kitchen screen.')
    state = fields.Selection([
        ('new', 'New'), ('preparing', 'Preparing'), ('ready', 'Ready'),
        ('done', 'Delivered'), ('cancel', 'Cancelled')], default='new', required=True, tracking=True)
    line_ids = fields.One2many('cafe.kitchen.order.line', 'order_id', string='Items')
    summary = fields.Text(compute='_compute_summary')
    date_received = fields.Datetime(default=fields.Datetime.now, readonly=True)
    date_started = fields.Datetime(readonly=True)
    date_ready = fields.Datetime(readonly=True)
    prep_minutes = fields.Float(compute='_compute_prep_minutes', string='Prep Time (min)')

    _sql_constraints = [
        ('pos_order_uniq', 'unique(pos_order_id)', 'A kitchen order already exists for this POS order.'),
    ]

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('cafe.kitchen.order') or '/'
        records = super().create(vals_list)
        records._notify_kitchen('new')
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            self._notify_kitchen('update')
        return res

    def _notify_kitchen(self, event):
        """Tell every open kitchen screen to refresh (Odoo bus, no polling)."""
        if not self:
            return
        self.env['bus.bus']._sendone('cafe_kitchen', 'cafe_kitchen_update', {
            'event': event, 'tickets': self.mapped('kitchen_ticket')})

    @api.depends('pos_order_id.sequence_number')
    def _compute_kitchen_ticket(self):
        # MUST match the JS formula in static/src/pos/order_patch.js
        for rec in self:
            rec.kitchen_ticket = 'K%03d' % (rec.pos_order_id.sequence_number or 0)

    @api.depends('line_ids.qty', 'line_ids.product_id', 'line_ids.note')
    def _compute_summary(self):
        for rec in self:
            rec.summary = '\n'.join(
                '%g x %s%s' % (l.qty, l.product_id.display_name, ' (%s)' % l.note if l.note else '')
                for l in rec.line_ids)

    @api.depends('date_received', 'date_ready')
    def _compute_prep_minutes(self):
        for rec in self:
            rec.prep_minutes = ((rec.date_ready - rec.date_received).total_seconds() / 60.0
                                if rec.date_ready and rec.date_received else 0.0)

    def _check_state(self, allowed):
        for rec in self:
            if rec.state not in allowed:
                raise UserError(_('Order %(n)s cannot go through this step from state "%(s)s".',
                                  n=rec.name, s=rec.state))

    def action_start(self):
        self._check_state(['new'])
        self.write({'state': 'preparing', 'date_started': fields.Datetime.now()})

    def action_ready(self):
        self._check_state(['new', 'preparing'])
        self.write({'state': 'ready', 'date_ready': fields.Datetime.now()})

    def action_done(self):
        self._check_state(['ready'])
        self.write({'state': 'done'})

    def action_cancel(self):
        self._check_state(['new', 'preparing'])
        self.write({'state': 'cancel'})


class CafeKitchenOrderLine(models.Model):
    _name = 'cafe.kitchen.order.line'
    _description = 'Cafe Kitchen Order Line'

    order_id = fields.Many2one('cafe.kitchen.order', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', required=True)
    qty = fields.Float(default=1.0)
    note = fields.Char()
