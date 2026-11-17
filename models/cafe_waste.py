from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class CafeWaste(models.Model):
    _name = 'cafe.waste'
    _description = 'Cafe Waste'
    _inherit = ['mail.thread']
    _order = 'date desc, id desc'

    name = fields.Char(default='/', readonly=True, copy=False)
    company_id = fields.Many2one('res.company', default=lambda s: s.env.company)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    location_id = fields.Many2one(
        'stock.location', string='Stock Location', required=True,
        domain="[('usage', '=', 'internal')]", default=lambda s: s._default_location())
    reason = fields.Selection([
        ('expired', 'Expired'), ('spilled', 'Spilled / Mistake'), ('damaged', 'Damaged'),
        ('staff', 'Staff Consumption'), ('other', 'Other')], default='spilled', required=True)
    state = fields.Selection([('draft', 'Draft'), ('done', 'Confirmed')], default='draft', tracking=True)
    line_ids = fields.One2many('cafe.waste.line', 'waste_id', string='Wasted Ingredients')
    move_ids = fields.One2many('stock.move', 'cafe_waste_id', readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    total_cost = fields.Monetary(compute='_compute_total_cost', store=True)
    note = fields.Text()

    @api.model
    def _default_location(self):
        wh = self.env['stock.warehouse'].search([('company_id', '=', self.env.company.id)], limit=1)
        return wh.lot_stock_id

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', '/') == '/':
                vals['name'] = self.env['ir.sequence'].next_by_code('cafe.waste') or '/'
        return super().create(vals_list)

    @api.depends('line_ids.cost')
    def _compute_total_cost(self):
        for rec in self:
            rec.total_cost = sum(rec.line_ids.mapped('cost'))

    def unlink(self):
        if any(r.state == 'done' for r in self):
            raise UserError(_('Confirmed waste records cannot be deleted.'))
        return super().unlink()

    def action_confirm(self):
        for rec in self:
            if rec.state == 'done':
                continue
            if not rec.line_ids:
                raise UserError(_('Add at least one ingredient.'))
            scrap = self.env['stock.location'].search([
                ('scrap_location', '=', True), ('company_id', 'in', [False, rec.company_id.id])], limit=1)
            if not scrap:
                raise UserError(_('No scrap location configured.'))
            moves = self.env['stock.move']
            for line in rec.line_ids:
                prod = line.ingredient_id.product_id
                moves |= self.env['stock.move'].sudo().create({
                    'name': _('Cafe waste: %s', rec.name), 'origin': rec.name,
                    'product_id': prod.id, 'product_uom': prod.uom_id.id,
                    'product_uom_qty': line.uom_id._compute_quantity(line.quantity, prod.uom_id),
                    'location_id': rec.location_id.id, 'location_dest_id': scrap.id,
                    'company_id': rec.company_id.id, 'cafe_waste_id': rec.id,
                })
            moves._action_confirm()
            moves._action_assign()
            for m in moves:
                m.quantity_done = m.product_uom_qty
            moves._action_done()
            rec.state = 'done'


class CafeWasteLine(models.Model):
    _name = 'cafe.waste.line'
    _description = 'Cafe Waste Line'

    waste_id = fields.Many2one('cafe.waste', required=True, ondelete='cascade')
    ingredient_id = fields.Many2one('cafe.ingredient', required=True)
    quantity = fields.Float(digits='Product Unit of Measure', required=True, default=1.0)
    uom_category_id = fields.Many2one(related='ingredient_id.product_id.uom_id.category_id')
    uom_id = fields.Many2one(
        'uom.uom', string='Unit', required=True, compute='_compute_uom_id', store=True,
        readonly=False, precompute=True, domain="[('category_id', '=', uom_category_id)]")
    cost = fields.Float(compute='_compute_cost', store=True)

    @api.depends('ingredient_id')
    def _compute_uom_id(self):
        for line in self:
            if line.ingredient_id and (not line.uom_id or line.uom_id.category_id != line.uom_category_id):
                line.uom_id = line.ingredient_id.product_id.uom_id

    @api.depends('quantity', 'uom_id', 'ingredient_id.standard_price')
    def _compute_cost(self):
        for line in self:
            prod = line.ingredient_id.product_id
            line.cost = (line.uom_id._compute_quantity(line.quantity, prod.uom_id, round=False)
                         * prod.standard_price) if prod and line.uom_id else 0.0

    @api.constrains('quantity')
    def _check_quantity(self):
        if any(l.quantity <= 0 for l in self):
            raise ValidationError(_('Wasted quantity must be positive.'))
