import { css, CSSResultGroup, html, LitElement, TemplateResult } from "lit";
import { customElement, state, property } from "lit/decorators";
// import { computeStateName } from "../../../common/entity/compute_state_name";
import "../../../components/entity/state-badge";
import type { ActionHandlerEvent } from "../../data/lovelace";
import type { HomeAssistant } from "../../types";
import type { EntitiesCardEntityConfig } from "../cards/types";
import { computeTooltip } from "../common/compute-tooltip";
import { actionHandler } from "../common/directives/action-handler-directive";
import { handleAction } from "../common/handle-action";
import { hasAction } from "../common/has-action";
import { computeObjectId } from "../../common/compute_object_id";

export declare type HassEntityBase = {
  entity_id: string;
  state: string;
  last_changed: string;
  last_updated: string;
  attributes: HassEntityAttributeBase;
  context: {
      id: string;
      user_id: string | null;
  };
};
export declare type HassEntityAttributeBase = {
  friendly_name?: string;
  unit_of_measurement?: string;
  icon?: string;
  entity_picture?: string;
  supported_features?: number;
  hidden?: boolean;
  assumed_state?: boolean;
  device_class?: string;
};
export declare type HassEntity = HassEntityBase & {
  attributes: {
      [key: string]: any;
  };
};
export const computeStateName = (stateObj: HassEntity): string =>
  stateObj.attributes.friendly_name === undefined
    ? computeObjectId(stateObj.entity_id).replace(/_/g, " ")
    : stateObj.attributes.friendly_name || "";

@customElement("hui-buttons-base")
export class HuiButtonsBase extends LitElement {
  @state() public hass!: HomeAssistant;

  @property() public configEntities?: EntitiesCardEntityConfig[];

  protected render(): TemplateResult {
    return html`
      ${(this.configEntities || []).map((entityConf) => {
        const stateObj = this.hass.states[entityConf.entity];

        return html`
          <div
            @action=${this._handleAction}
            .actionHandler=${actionHandler({
              hasHold: hasAction(entityConf.hold_action),
              hasDoubleClick: hasAction(entityConf.double_tap_action),
            })}
            .config=${entityConf}
            tabindex="0"
          >
            ${entityConf.show_icon !== false
              ? html`
                  <state-badge
                    title=${computeTooltip(this.hass, entityConf)}
                    .hass=${this.hass}
                    .stateObj=${stateObj}
                    .overrideIcon=${entityConf.icon}
                    .overrideImage=${entityConf.image}
                    stateColor
                  ></state-badge>
                `
              : ""}
            <span>
              ${(entityConf.show_name && stateObj) ||
              (entityConf.name && entityConf.show_name !== false)
                ? entityConf.name || computeStateName(stateObj)
                : ""}
            </span>
          </div>
        `;
      })}
    `;
  }

  private _handleAction(ev: ActionHandlerEvent) {
    const config = (ev.currentTarget as any).config as EntitiesCardEntityConfig;
    handleAction(this, this.hass, config, ev.detail.action!);
  }

  static get styles(): CSSResultGroup {
    return css`
      :host {
        display: flex;
        justify-content: space-evenly;
      }
      div {
        cursor: pointer;
        align-items: center;
        display: inline-flex;
        outline: none;
      }
    `;
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "hui-buttons-base": HuiButtonsBase;
  }
}
