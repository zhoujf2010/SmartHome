import { HassEntity } from "../../../core/type";
import { computeDomain } from "./compute_domain";

export const computeStateDomain = (stateObj: HassEntity) =>
  computeDomain(stateObj.entity_id);
