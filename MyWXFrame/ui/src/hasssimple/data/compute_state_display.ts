// import { HassEntity } from "home-assistant-js-websocket";
import { UNAVAILABLE, UNKNOWN } from "./entity";
import { FrontendLocaleData } from "./translation";
import { formatDate } from "../common/datetime/format_date";
import { formatDateTime } from "../common/datetime/format_date_time";
import { formatTime } from "../common/datetime/format_time";
import { formatNumber } from "../common/string/format_number";
import { LocalizeFunc } from "../common/translations/localize";
// import { computeStateDomain } from "./compute_state_domain";
export const computeDomain = (entityId: string): string =>
  entityId.substr(0, entityId.indexOf("."));

  
export const computeStateDomain = (stateObj: HassEntity) =>
  computeDomain(stateObj.entity_id);

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

export const computeStateDisplay = (
  localize: LocalizeFunc,
  stateObj: HassEntity,
  locale: FrontendLocaleData,
  state?: string
): string => {
  const compareState = state !== undefined ? state : stateObj.state;

  if (compareState === UNKNOWN || compareState === UNAVAILABLE) {
    return localize(`state.default.${compareState}`);
  }

  if (stateObj.attributes.unit_of_measurement) {
    if (stateObj.attributes.device_class === "monetary") {
      try {
        return formatNumber(compareState, locale, {
          style: "currency",
          currency: stateObj.attributes.unit_of_measurement,
        });
      } catch (_err) {
        // fallback to default
      }
    }
    return `${formatNumber(compareState, locale)} ${
      stateObj.attributes.unit_of_measurement
    }`;
  }

  const domain = computeStateDomain(stateObj);

  if (domain === "input_datetime") {
    if (state) {
      // If trying to display an explicit state, need to parse the explict state to `Date` then format.
      // Attributes aren't available, we have to use `state`.
      try {
        const components = state.split(" ");
        if (components.length === 2) {
          // Date and time.
          return formatDateTime(new Date(components.join("T")), locale);
        }
        if (components.length === 1) {
          if (state.includes("-")) {
            // Date only.
            return formatDate(new Date(`${state}T00:00`), locale);
          }
          if (state.includes(":")) {
            // Time only.
            const now = new Date();
            return formatTime(
              new Date(`${now.toISOString().split("T")[0]}T${state}`),
              locale
            );
          }
        }
        return state;
      } catch {
        // Formatting methods may throw error if date parsing doesn't go well,
        // just return the state string in that case.
        return state;
      }
    } else {
      // If not trying to display an explicit state, create `Date` object from `stateObj`'s attributes then format.
      let date: Date;
      if (!stateObj.attributes.has_time) {
        date = new Date(
          stateObj.attributes.year,
          stateObj.attributes.month - 1,
          stateObj.attributes.day
        );
        return formatDate(date, locale);
      }
      if (!stateObj.attributes.has_date) {
        date = new Date();
        date.setHours(stateObj.attributes.hour, stateObj.attributes.minute);
        return formatTime(date, locale);
      }

      date = new Date(
        stateObj.attributes.year,
        stateObj.attributes.month - 1,
        stateObj.attributes.day,
        stateObj.attributes.hour,
        stateObj.attributes.minute
      );
      return formatDateTime(date, locale);
    }
  }

  if (domain === "humidifier") {
    if (compareState === "on" && stateObj.attributes.humidity) {
      return `${stateObj.attributes.humidity} %`;
    }
  }

  // `counter` `number` and `input_number` domains do not have a unit of measurement but should still use `formatNumber`
  if (
    domain === "counter" ||
    domain === "number" ||
    domain === "input_number"
  ) {
    return formatNumber(compareState, locale);
  }

  return (
    // Return device class translation
    (stateObj.attributes.device_class &&
      localize(
        `component.${domain}.state.${stateObj.attributes.device_class}.${compareState}`
      )) ||
    // Return default translation
    localize(`component.${domain}.state._.${compareState}`) ||
    // We don't know! Return the raw state.
    compareState
  );
};
