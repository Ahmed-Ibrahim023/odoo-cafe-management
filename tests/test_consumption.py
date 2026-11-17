from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestCafeConsumption(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        env = cls.env
        wh = env['stock.warehouse'].search([('company_id', '=', env.company.id)], limit=1)
        cls.stock_loc = wh.lot_stock_id
        kg = env.ref('uom.product_uom_kgm')
        gram = env.ref('uom.product_uom_gram')

        cls.beans = env['product.product'].create({
            'name': 'Test Beans', 'detailed_type': 'product', 'uom_id': kg.id,
            'uom_po_id': kg.id, 'standard_price': 600})
        env['stock.quant']._update_available_quantity(cls.beans, cls.stock_loc, 10.0)
        cls.ingredient = env['cafe.ingredient'].create({'name': 'Test Beans', 'product_id': cls.beans.id})

        cls.drink = env['product.product'].create({
            'name': 'Test Cappuccino', 'detailed_type': 'consu',
            'list_price': 80, 'available_in_pos': True})
        cls.recipe = env['cafe.recipe'].create({
            'product_tmpl_id': cls.drink.product_tmpl_id.id,
            'line_ids': [(0, 0, {'ingredient_id': cls.ingredient.id, 'quantity': 18, 'uom_id': gram.id})],
        })
        cls.config = env['pos.config'].create({'name': 'Cafe Test POS'})
        cls.config.open_ui()
        cls.session = cls.config.current_session_id

    def _paid_order(self, qty):
        total = 80.0 * qty
        order = self.env['pos.order'].create({
            'session_id': self.session.id, 'company_id': self.env.company.id,
            'pricelist_id': self.config.pricelist_id.id,
            'amount_tax': 0.0, 'amount_total': total, 'amount_paid': 0.0, 'amount_return': 0.0,
            'lines': [(0, 0, {
                'product_id': self.drink.id, 'qty': qty, 'price_unit': 80.0,
                'price_subtotal': total, 'price_subtotal_incl': total})],
        })
        order.add_payment({
            'pos_order_id': order.id, 'amount': total,
            'payment_method_id': self.config.payment_method_ids[0].id})
        order.action_pos_order_paid()
        return order

    def _on_hand(self):
        return self.env['stock.quant']._get_available_quantity(self.beans, self.stock_loc)

    def test_recipe_cost(self):
        # 18 g of beans at 600 / kg = 10.8
        self.assertAlmostEqual(self.recipe.cost, 10.8, places=4)

    def test_deduction_with_uom_conversion(self):
        order = self._paid_order(3)           # 3 x 18 g = 54 g = 0.054 kg
        self.assertTrue(order.cafe_consumed, order.cafe_error)
        self.assertAlmostEqual(self._on_hand(), 10.0 - 0.054, places=4)
        self.assertEqual(len(order.cafe_move_ids), 1)
        self.assertTrue(order.cafe_kitchen_order_id)
        self.assertAlmostEqual(order.cafe_cost, 3 * 10.8, places=4)

    def test_no_double_deduction(self):
        order = self._paid_order(1)
        after_first = self._on_hand()
        order._cafe_process_paid_order()
        order.action_cafe_retry()
        self.assertAlmostEqual(self._on_hand(), after_first, places=6)
        self.assertEqual(len(order.cafe_move_ids), 1)

    def test_availability_check(self):
        Order = self.env['pos.order']
        ok = Order.cafe_check_availability(self.config.id, [{'product_id': self.drink.id, 'qty': 3}])
        self.assertTrue(ok['ok'])
        # 1000 drinks = 18 kg of beans, only 10 kg in stock
        bad = Order.cafe_check_availability(self.config.id, [{'product_id': self.drink.id, 'qty': 1000}])
        self.assertFalse(bad['ok'])
        self.assertEqual(bad['shortages'][0]['name'], 'Test Beans')
        self.assertAlmostEqual(bad['shortages'][0]['needed'], 18.0, places=3)
        # refunds never block
        neg = Order.cafe_check_availability(self.config.id, [{'product_id': self.drink.id, 'qty': -1000}])
        self.assertTrue(neg['ok'])
        # switch off
        self.config.cafe_block_insufficient_stock = False
        off = Order.cafe_check_availability(self.config.id, [{'product_id': self.drink.id, 'qty': 1000}])
        self.assertTrue(off['ok'])

    def test_kitchen_ticket_matches_sequence(self):
        order = self._paid_order(1)
        self.assertEqual(order.cafe_kitchen_order_id.kitchen_ticket, 'K%03d' % order.sequence_number)
