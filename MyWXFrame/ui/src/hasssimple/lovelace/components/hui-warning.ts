// import { STATE_NOT_RUNNING } from "home-assistant-js-websocket";
declare const STATE_NOT_RUNNING = "NOT_RUNNING";
import { css, CSSResultGroup, html, LitElement, TemplateResult } from "lit";
import { customElement } from "lit/decorators";
import type { HomeAssistant } from "../../common/types";

export const createEntityNotFoundWarning = (
  hass: HomeAssistant,
  entityId: string
) =>
  "实体未找到"
  // hass.config.state !== STATE_NOT_RUNNING
  //   ? hass.localize(
  //       "ui.panel.lovelace.warning.entity_not_found",
  //       "entity",
  //       entityId || "[empty]"
  //     )
  //   : hass.localize("ui.panel.lovelace.warning.starting");

@customElement("hui-warning")
export class HuiWarning extends LitElement {
  protected render(): TemplateResult {
    return html` <slot></slot> `;
  }

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: block;
        color: black;
        background-color: #fce588;
        padding: 8px;
        word-break: break-word;
      }
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "hui-warning": HuiWarning;
  }
}
