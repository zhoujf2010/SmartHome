import "@material/mwc-button";
import "@material/mwc-list/mwc-list-item";
import "@polymer/app-layout/app-header/app-header";
import "@polymer/app-layout/app-scroll-effects/effects/waterfall";
import "@polymer/app-layout/app-toolbar/app-toolbar";
import "@polymer/paper-tabs/paper-tab";
import "@polymer/paper-tabs/paper-tabs";
import {
  css,
  CSSResultGroup,
  html,
  LitElement,
  TemplateResult,
} from "lit";
import { property, state, } from "lit/decorators";
import { navigate } from "../../common/navigate";
import "../../components/ha-tabs";
import type {
  LovelaceConfig
} from "../../data/lovelace";
import "../../layouts/ha-app-layout";
import { haStyle } from "../../resources/styles";
import type { HomeAssistant } from "../../types";
import type { Lovelace } from "./types";
import "./views/hui-view";
import {
  fetchConfig,
} from "../../data/lovelace";


class HUIRoot extends LitElement {
  @property({ attribute: false }) public hass!: HomeAssistant;

  @state() public lovelace?: Lovelace;

  @property({ type: Boolean }) public narrow = false;

  @property() public route?: { path: string; prefix: string };

  @state() private _curView?: number | "hass-unused-entities";
  @state() private config: LovelaceConfig;

  constructor() {
    super();
  }

  protected render(): TemplateResult {
    console.log("currentIndex=" + this._curView);
    if (!this.config)
      return html``;

    return html`
      <ha-app-layout id="layout">
        <app-header slot="header" effects="waterfall" fixed condenses>
          <app-toolbar>
            <ha-tabs scrollable .selected="${this._curView}"
              @iron-activate="${this._handleViewSelected}">
              ${this.config.views.map(
      (view) => html`<paper-tab>${view.title}</paper-tab>`)}
            </ha-tabs>
          </app-toolbar>
        </app-header>
        <hui-view .index=${this._curView}
        .lovelace=${this.lovelace}
        .hass=${this.hass}
        .narrow=false
        ></hui-view>
      </ha-app-layout>
    `;
  }

  protected async firstUpdated() {
    this._curView = 0;
    let confProm = fetchConfig(
      this.hass!.connection,
      null,
      true
    );
    this.config = await confProm;
    console.log(this.config);

    this.lovelace = {
      config: this.config,
      rawConfig: this.config,
      mode: "storage",
      urlPath: null,
      editMode: this.lovelace ? this.lovelace.editMode : false,
      locale: this.hass!.locale,
      enableFullEditMode: () => { },
      setEditMode: () => { },
      saveConfig: async (): Promise<void> => { },
      deleteConfig: async (): Promise<void> => { },
    };
  }

  private _handleViewSelected(ev) {
    const viewIndex = ev.detail.selected as number;
    if (viewIndex !== this._curView) {
      const path = this.config.views[viewIndex].path || viewIndex;
      this._curView = viewIndex;
      navigate(`${this.route!.prefix}/${path}`);
    }
  }

  static get styles(): CSSResultGroup {
    return [
      haStyle,
      css`
        :host {
          -ms-user-select: none;
          -webkit-user-select: none;
          -moz-user-select: none;
        }

        ha-app-layout {
          min-height: 100%;
        }
        ha-tabs {
          width: 100%;
          height: 100%;
          margin-left: 4px;
        }
        paper-tabs {
          margin-left: 12px;
          margin-left: max(env(safe-area-inset-left), 12px);
          margin-right: env(safe-area-inset-right);
        }
        ha-tabs,
        paper-tabs {
          --paper-tabs-selection-bar-color: var(
            --app-header-selection-bar-color,
            var(--app-header-text-color, #fff)
          );
          text-transform: uppercase;
        }

        .edit-mode app-header,
        .edit-mode app-toolbar {
          background-color: var(--app-header-edit-background-color, #455a64);
          color: var(--app-header-edit-text-color, #fff);
        }
        .edit-mode div[main-title] {
          pointer-events: auto;
        }
        paper-tab.iron-selected .edit-icon {
          display: inline-flex;
        }
        .edit-icon {
          color: var(--accent-color);
          padding-left: 8px;
          vertical-align: middle;
          --mdc-theme-text-disabled-on-light: var(--disabled-text-color);
        }
        .edit-icon.view {
          display: none;
        }
        #add-view {
          position: absolute;
          height: 44px;
        }
        #add-view ha-svg-icon {
          background-color: var(--accent-color);
          border-radius: 4px;
        }
        app-toolbar a {
          color: var(--text-primary-color, white);
        }
        mwc-button.warning:not([disabled]) {
          color: var(--error-color);
        }
        #view {
          min-height: calc(100vh - var(--header-height));
          /**
          * Since we only set min-height, if child nodes need percentage
          * heights they must use absolute positioning so we need relative
          * positioning here.
          *
          * https://www.w3.org/TR/CSS2/visudet.html#the-height-property
          */
          position: relative;
          display: flex;
        }
        /**
         * In edit mode we have the tab bar on a new line *
         */
        .edit-mode #view {
          min-height: calc(100vh - var(--header-height) - 48px);
        }
        #view > * {
          /**
          * The view could get larger than the window in Firefox
          * to prevent that we set the max-width to 100%
          * flex-grow: 1 and flex-basis: 100% should make sure the view
          * stays full width.
          *
          * https://github.com/home-assistant/home-assistant-polymer/pull/3806
          */
          flex: 1 1 100%;
          max-width: 100%;
        }
        .hide-tab {
          display: none;
        }
        .menu-link {
          text-decoration: none;
        }
        hui-view {
          background: var(
            --lovelace-background,
            var(--primary-background-color)
          );
        }
      `,
    ];
  }
}

declare global {
  interface HTMLElementTagNameMap {
    "hui-root": HUIRoot;
  }
}

customElements.define("hui-root", HUIRoot);
