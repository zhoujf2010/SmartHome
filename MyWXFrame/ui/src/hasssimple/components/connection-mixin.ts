import { HassBaseEl, Constructor,HomeAssistant,ServiceCallResponse } from "../state/hass-base-mixin";
import { Auth } from "./auth";
// import {Connection } from "./Connection";
import hassCallApi from "./Connection";

import {
  subscribeEntities,
  Connection,callService
} from "../home-assistant-js-websocket";

export default <T extends Constructor<HassBaseEl>>(
    superClass: T
) =>
    class extends superClass {
        protected initializeHass(auth: Auth, conn: Connection) {
            
        // @ts-ignore: Unreachable code error
            this.hass = {
                auth,
                states: null as any,
                connection: conn,
                connected: true,
                hassUrl: (path = "") => new URL(path, auth.data.hassUrl).toString(),
                callApi: async (method, path, parameters, headers) =>
                  hassCallApi(auth, method, path, parameters, headers),
                sendWS: (msg) => {
                      // eslint-disable-next-line no-console
                    console.log("Sending", msg);
                    conn.sendMessage(msg);
                  },
                  callService: async (domain, service, serviceData = {}, target) => {
                    // if (__DEV__) {
                      // eslint-disable-next-line no-console
                      console.log(
                        "Calling service",
                        domain,
                        service,
                        serviceData,
                        target
                      );
                    // }
                    try {
                      return (await callService(
                        conn,
                        domain,
                        service,
                        serviceData,
                        target
                      )) as ServiceCallResponse;
                    } catch (err) {
                      // if (
                      //   err.error?.code === ERR_CONNECTION_LOST &&
                      //   serviceCallWillDisconnect(domain, service)
                      // ) {
                        return { context: { id: "" } };
                      // }
                      // if (__DEV__) {
                      //   // eslint-disable-next-line no-console
                      //   console.error(
                      //     "Error calling service",
                      //     domain,
                      //     service,
                      //     serviceData,
                      //     target,
                      //     err
                      //   );
                      // }
                      // forwardHaptic("failure");
                      // const message =
                      //   (this as any).hass.localize(
                      //     "ui.notification_toast.service_call_failed",
                      //     "service",
                      //     `${domain}/${service}`
                      //   ) + ` ${err.message}`;
                      // fireEvent(this as any, "hass-notification", { message });
                      // throw err;
                    }
                  },
            };
            // console.log("xxx"+`${this.hass}`)
      

            this.hassConnected();
        }

        protected hassConnected() {
          super.hassConnected();
    
          const conn = this.hass!.connection;
          // @ts-ignore: Unreachable code error
          subscribeEntities(conn, (states) => this._updateHass({ states }));
        }
    };
