/** @odoo-module **/
import { registry } from "@web/core/registry";
import { kanbanView } from "@web/views/kanban/kanban_view";
import { KanbanController } from "@web/views/kanban/kanban_controller";
import { onWillUnmount } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";

function beep() {
    try {
        const ctx = new (window.AudioContext || window.webkitAudioContext)();
        const osc = ctx.createOscillator();
        osc.frequency.value = 880;
        osc.connect(ctx.destination);
        osc.start();
        osc.stop(ctx.currentTime + 0.15);
    } catch (e) {
        /* sound is optional (browser autoplay policy) */
    }
}

const CHANNEL = "cafe_kitchen";
const EVENT = "cafe_kitchen_update";

export class CafeKitchenKanbanController extends KanbanController {
    setup() {
        super.setup();
        // Raw services on purpose: avoids useService() wrapper issues across builds.
        const bus = this.env.services.bus_service;
        const notification = this.env.services.notification;
        this._alive = true;

        bus.addChannel(CHANNEL);
        const unsubscribe = bus.subscribe(EVENT, async (payload) => {
            if (!this._alive) {
                return;
            }
            await this.model.load();
            this.model.notify();
            if (payload && payload.event === "new") {
                beep();
                notification.add(_t("New order: %s", (payload.tickets || []).join(", ")), {
                    type: "info",
                });
            }
        });

        onWillUnmount(() => {
            this._alive = false;
            if (typeof unsubscribe === "function") {
                unsubscribe();
            }
            bus.deleteChannel(CHANNEL);
        });
    }
}

registry.category("views").add("cafe_kitchen_kanban", {
    ...kanbanView,
    Controller: CafeKitchenKanbanController,
});
