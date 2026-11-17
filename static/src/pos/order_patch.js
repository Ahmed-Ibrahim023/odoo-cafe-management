/** @odoo-module */
import { Order } from "@point_of_sale/app/store/models";
import { patch } from "@web/core/utils/patch";

patch(Order.prototype, {
    export_for_printing() {
        const result = super.export_for_printing(...arguments);
        const hasKitchenItem = this.get_orderlines().some(
            (line) => line.get_product().cafe_in_kitchen
        );
        if (hasKitchenItem) {
            // MUST match cafe.kitchen.order._compute_kitchen_ticket (python)
            result.cafe_kitchen_ticket = "K" + String(this.sequence_number).padStart(3, "0");
        }
        return result;
    },
});
