/** @odoo-module */
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";

patch(PaymentScreen.prototype, {
    // Last safety net: quantities edited with the numpad bypass addProductToCurrentOrder.
    async _isOrderValid(isForceValidate) {
        const valid = await super._isOrderValid(...arguments);
        if (!valid) {
            return false;
        }
        return await this.pos.cafeCheckAvailability(this.currentOrder);
    },
});
