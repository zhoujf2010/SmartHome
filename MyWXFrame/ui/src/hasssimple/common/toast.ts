import { fireEvent } from "./dom/fire_event";
// import { ShowToastParams } from "../managers/notification-manager";

export const showToast = (el: HTMLElement, params: any) =>
// @ts-ignore: Unreachable code error
  fireEvent(el, "hass-notification", params);
