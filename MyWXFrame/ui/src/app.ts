import { html, LitElement, PropertyValues } from "lit";
import { property, state } from "lit/decorators";

import "@material/mwc-button";

import { HomeAssistant, HassEntities, ServiceCallResponse, HassServiceTarget } from "./core/type";
import { askWrite } from "./core/token_storage";
import { Auth, clearTokens, fetchToken } from "./core/auth";
import { Connection, createSocket } from "./core/Connection";
import "./hasssimple/hui-root";
import { AuthData, QueryCallbackData, parseQuery } from "./core/type";

import {
  subscribeEntities
} from "./core/entities";

import * as messages from "./core/messages";

export const callService = (
  connection: Connection,
  domain: string,
  service: string,
  serviceData?: object,
  target?: HassServiceTarget
) =>
  connection.sendMessagePromise(
    messages.callService(domain, service, serviceData, target)
  );


//用这个可以屏蔽一些报错// @ts-ignore: Unreachable code error

declare global {
  interface Window {
    hassConnection: Promise<{ auth: Auth; conn: Connection } | any>;
  }
}

class testctl extends LitElement {

  @state() private hass?: HomeAssistant;
  @state() private status: string;

  constructor() {
    super();
    this.status = "init";
  }

  protected render() {
    let curpath = "";
    if (location.pathname.includes("MyWx/lovelace"))
      curpath = location.pathname.substring("MyWx/lovelace".length + 2);

    const rrr = {
      prefix: "/MyWx/lovelace",
      path: curpath,  //xxx
    };
    if (this.status == "init")
      return html`初使化中`;
    if (this.status == "noauth")
      return html`无权访问`;

    if (!this.hass)
      return html``;
    else
      return html` 
      <hui-root
        .hass=${this.hass}
        .route=${rrr}
        .narrow=false
      ></hui-root>
        `;
  }

  protected async firstUpdated(changedProps: PropertyValues) {
    const result = await window.hassConnection;
    console.log("result->" + result);
    if (result == null) {
      this.status = "noauth";
      return;
    }

    this.hass = {
      auth: result?.auth,
      connection: result?.conn,
      connected: true,
      states: null as any,
      hassUrl: (path = "") => new URL(path, result?.auth.data.hassUrl).toString(),
      callApi: async (method, path, parameters, headers) => result?.conn.hassCallApi(result?.auth, method, path, parameters, headers),
      sendWS: async (msg) => result?.conn.sendMessagePromise(msg),
      callService: async (domain: any, service: any, serviceData = {}, target: any) => {
        return (await callService(result?.conn, domain, service, serviceData, target)) as ServiceCallResponse;
      },
    };

    subscribeEntities(result?.conn, (states) => this._updateHass(states));

    this.status = "OK";
  }

  protected _updateHass(obj: HassEntities) {
    if (this.hass) {
      const dt = { "states": obj };
      this.hass = { ...this.hass, ...dt };
    }
  }
}

customElements.define("demo-ctl", testctl);

export async function getAuth(hassUrl: string) {
  try {

    const clientId = `${location.protocol}//${location.host}/`;

    //模拟登陆，获取token
    const query = parseQuery<QueryCallbackData>(location.search.substr(1));
    if (!("code" in query))
      return null;

    const response3 = await fetch(hassUrl + "/auth/login_flow", {
      method: "POST",
      credentials: "same-origin",
      body: JSON.stringify({
        client_id: clientId,
        redirect_uri: "",
      }),
    });
    const dt = await response3.json();

    const response = await fetch(hassUrl + `/auth/login_flow/${dt.flow_id}`, {
      method: "POST",
      credentials: "same-origin",
      body: JSON.stringify({
        code: query.code,
        client_id: clientId,
      }),
    });

    const newStep = await response.json();
    const data = await fetchToken(hassUrl, clientId, newStep.result);

    return new Auth(data);
  }
  catch (error) {
    console.log(error);
    return null;
  }
}

const connProm = async (auth: any) => {
  try {
    if (auth == null)
      throw new Error("no log");

    const socket = await createSocket(auth); //创建websocket连接
    const conn = new Connection(socket, auth);

    if (location.search.includes("auth_callback=1")) {
      const searchParams = new URLSearchParams(location.search);
      searchParams.delete("auth_callback");
      searchParams.delete("code");
      searchParams.delete("state");
      const param = searchParams.toString();
      let url = `${location.pathname}`;
      if (param != "")
        url = url + '?' + param;
      history.replaceState(null, "", url);
    }

    return { auth, conn };

  } catch (error) {
    clearTokens();
    //未登陆，跳转至登陆页面
    // document.location!.href = getRedirectURL();
    return null;
  }
};

const hassUrl = `${location.protocol}//${location.host}/MyWx`;
window.hassConnection = getAuth(hassUrl).then(connProm);