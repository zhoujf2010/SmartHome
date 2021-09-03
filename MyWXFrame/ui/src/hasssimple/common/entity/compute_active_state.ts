import { HassEntity } from "../../../core/type";

export const computeActiveState = (stateObj: HassEntity): string => {
  const domain = stateObj.entity_id.split(".")[0];
  let state = stateObj.state;

  if (domain === "climate") {
    state = stateObj.attributes.hvac_action;
  }

  return state;
};
