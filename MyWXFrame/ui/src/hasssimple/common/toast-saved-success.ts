import { HomeAssistant } from "../common/types";
import { showToast } from "./toast";

export const showSaveSuccessToast = (el: HTMLElement, hass: HomeAssistant) =>
  showToast(el, {
    message: hass!.localize("ui.common.successfully_saved"),
  });
