import {PropertyValues} from "lit"
import { HassBaseEl ,Constructor} from "../state/hass-base-mixin";
import { askWrite } from "./token_storage";

declare global {
  // for fire event
  interface HASSDomEvents {
    "hass-refresh-current-user": undefined;
  }
}
export default <T extends Constructor<HassBaseEl>>(superClass: T) =>
  class extends superClass {

    protected firstUpdated(changedProps:PropertyValues) {
      super.firstUpdated(changedProps);
      // this.addEventListener("hass-logout", () => this._handleLogout());
    //   this.addEventListener("hass-refresh-current-user", () => {
    //     userCollection(this.hass!.connection).refresh();
    //   });
    }

    protected hassConnected() {
      super.hassConnected();
    //   subscribeUser(this.hass!.connection, (user) =>
    //     this._updateHass({ user })
    //   );

    // console.log("111122xs")
      if (askWrite()) {
        this.updateComplete
          .then(() => import("./auth-card"))
          .then(() => {
            const el = document.createElement("ha-store-auth-card");
            this.provideHass(el);
            document.body.appendChild(el);
          });
      }
    }

    private async _handleLogout() {
      try {
        await this.hass!.auth.revoke();
        // this.hass!.connection.close();
        // clearState();
        document.location.href = "/";
      } catch (err) {
        // eslint-disable-next-line
        console.error(err);
        alert("Log out failed");
      }
    }
  };
