# cafe_management (Odoo 17)

Recipes + automatic ingredient deduction on top of the standard Point of Sale.

## Install
1. Copy `cafe_management` into your addons path, restart Odoo, Update Apps List.
2. Install "Cafe Management" (depends on point_of_sale, stock, account).
3. Run tests: `odoo -d DB -i cafe_management --test-tags /cafe_management --stop-after-init`

## Flow
Ingredients (linked to storable products) -> Recipe on a POS product -> sell in POS.
When the POS order is paid (online or synced after offline), the module:
creates a kitchen order, deducts ingredients via stock moves linked to the order
(`stock.move.cafe_pos_order_id`), stores ingredient cost per line and gross profit.

## Design notes
* Idempotent: `pos.order.cafe_consumed` flag + one move set per order.
* Never blocks a sale: errors are saved in `cafe_error` and retried by cron / button.
* Refunds: ingredients are NOT returned by default (the drink was made); set system
  parameter `cafe_management.restock_on_refund` = True to put them back.
* Sizes: create a recipe per product variant (Size attribute). Variant recipe wins over template recipe.
* Extras (Extra Shot / Extra Milk): create them as separate POS products with their own recipe.
* Multi-branch: stock is taken from the POS config's operation type source location.
* Receipt: native POS receipt is unchanged; a PDF 80mm receipt is available from Print on a POS order.

## Phase 2
* Kitchen screen is live: `cafe.kitchen.order` pushes `cafe_kitchen_update` on the Odoo bus
  (channel `cafe_kitchen`); the custom kanban (`js_class="cafe_kitchen_kanban"`) reloads and beeps on new orders.
* POS receipt shows "Kitchen Ticket Kxxx" (= `K` + order sequence number, computed the same way in JS and Python,
  so it also works offline and on reprints).
* Stock guard: `pos.order.cafe_check_availability` is called by the POS when adding a drink and again on payment
  validation. Switch it per POS in Point of Sale > Configuration (field "Block Sale When Ingredients Are Missing").
  If the POS cannot reach the server the sale is NOT blocked.
