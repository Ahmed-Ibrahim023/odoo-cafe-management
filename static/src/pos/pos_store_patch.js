/** @odoo-module */
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { ErrorPopup } from "@point_of_sale/app/errors/popups/error_popup";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    /**
     * Ask the server whether the ingredients for `order` (+ an optional extra
     * product about to be added) are in stock. Returns true when the sale may go on.
     * If the server is unreachable (offline POS) we never block the cashier.
     */
    async cafeCheckAvailability(order, extra = null) {
        if (!this.config.cafe_block_insufficient_stock) {
            return true;
        }
        const totals = new Map();
        let relevant = false;
        const add = (productId, qty, inKitchen) => {
            if (qty <= 0) {
                return;
            }
            relevant = relevant || inKitchen;
            totals.set(productId, (totals.get(productId) || 0) + qty);
        };
        if (order) {
            for (const line of order.get_orderlines()) {
                const product = line.get_product();
                add(product.id, line.get_quantity(), product.cafe_in_kitchen);
            }
        }
        if (extra) {
            add(extra.product.id, extra.qty, extra.product.cafe_in_kitchen);
        }
        if (!relevant) {
            return true;
        }
        const lines = [...totals].map(([product_id, qty]) => ({ product_id, qty }));
        let result;
        try {
            result = await this.orm.call("pos.order", "cafe_check_availability", [
                this.config.id,
                lines,
            ]);
        } catch (error) {
            return true; // offline / server error: let the sale continue
        }
        if (result.ok) {
            return true;
        }
        const body = result.shortages
            .map(
                (s) =>
                    `${s.name}: ${_t("needed")} ${s.needed} ${s.uom}, ` +
                    `${_t("available")} ${s.available} ${s.uom}`
            )
            .join("\n");
        await this.popup.add(ErrorPopup, { title: _t("Not enough ingredients"), body });
        return false;
    },

    async addProductToCurrentOrder(product, options = {}) {
        if (product.cafe_in_kitchen) {
            const ok = await this.cafeCheckAvailability(this.get_order(), {
                product,
                qty: options.quantity || 1,
            });
            if (!ok) {
                return;
            }
        }
        return super.addProductToCurrentOrder(...arguments);
    },
});
