
import { Auth } from "./auth";
import {  Connection } from "./Connection";
// import { HaFormSchema } from "../components/ha-form/ha-form";

export type UnsubscribeFunc = () => void;


export declare type MessageBase = {
    id?: number;
    type: string;
    [key: string]: any;
  };

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
  
export declare type HassEntities = {
  [entity_id: string]: HassEntity;
};


export interface ServiceCallRequest {
  domain: string;
  service: string;
  serviceData?: Record<string, any>;
  target?: HassServiceTarget;
}


export interface Context {
  id: string;
  parent_id?: string;
  user_id?: string | null;
}

export interface ServiceCallResponse {
  context: Context;
}

export interface HomeAssistant {
    auth: Auth;
    connection: Connection;
    connected: boolean;
    states: HassEntities;
    hassUrl(path?: string): string;
    callApi<T>(
      method: "GET" | "POST" | "PUT" | "DELETE",
      path: string,
      parameters?: Record<string, any>,
      headers?: Record<string, string>
    ): Promise<T>;
    sendWS<T>(msg: MessageBase): Promise<T>;
    callService(
      domain: ServiceCallRequest["domain"],
      service: ServiceCallRequest["service"],
      serviceData?: ServiceCallRequest["serviceData"],
      target?: ServiceCallRequest["target"]
    ): Promise<ServiceCallResponse>;
  }

  export type HassEventBase = {
    origin: string;
    time_fired: string;
    context: {
      id: string;
      user_id: string;
    };
  };
  
  export type StateChangedEvent = HassEventBase & {
    event_type: "state_changed";
    data: {
      entity_id: string;
      new_state: HassEntity | null;
      old_state: HassEntity | null;
    };
  };

export interface DiscoveryInformation {
    name: string;
    location_name: string;
    version: string;
  }
  
export interface DataEntryFlowStepForm {
    type: "form";
    flow_id: string;
    handler: string;
    step_id: string;
    data_schema: HaFormSchema[];
    errors: Record<string, string>;
    description_placeholders: Record<string, string>;
    last_step: boolean | null;
    }

    
export type AuthData = {
    hassUrl: string;
    clientId: string | null;
    expires: number;
    refresh_token: string;
    access_token: string;
    expires_in: number;
  };
  
export type SaveTokensFunc = (data: AuthData | null) => void;
export type LoadTokensFunc = () => Promise<AuthData | null | undefined>;

export type getAuthOptions = {
  hassUrl?: string;
  clientId?: string | null;
  redirectUrl?: string;
  authCode?: string;
  saveTokens?: SaveTokensFunc;
  loadTokens?: LoadTokensFunc;
};





export type QueryCallbackData =
  | {}
  | {
    state: string;
    code: string;
    auth_callback: string;
  };

export type AuthorizationCodeRequest = {
  grant_type: "authorization_code";
  code: string;
};

export type RefreshTokenRequest = {
  grant_type: "refresh_token";
  refresh_token: string;
};


export type Error = 1 | 2 | 3 | 4;


export type HassServiceTarget = {
  entity_id?: string | string[];
  device_id?: string | string[];
  area_id?: string | string[];
};



export type HaFormSchema =
  | HaFormConstantSchema
  | HaFormStringSchema
  | HaFormIntegerSchema
  | HaFormFloatSchema
  | HaFormBooleanSchema
  | HaFormSelectSchema
  | HaFormMultiSelectSchema
  | HaFormTimeSchema;

  
export interface HaFormBaseSchema {
  name: string;
  default?: HaFormData;
  required?: boolean;
  optional?: boolean;
  description?: { suffix?: string; suggested_value?: HaFormData };
}

export interface HaFormConstantSchema extends HaFormBaseSchema {
  type: "constant";
  value: string;
}

export interface HaFormIntegerSchema extends HaFormBaseSchema {
  type: "integer";
  default?: HaFormIntegerData;
  valueMin?: number;
  valueMax?: number;
}

export interface HaFormSelectSchema extends HaFormBaseSchema {
  type: "select";
  options?: string[] | Array<[string, string]>;
}

export interface HaFormMultiSelectSchema extends HaFormBaseSchema {
  type: "multi_select";
  options?: Record<string, string> | string[] | Array<[string, string]>;
}

export interface HaFormFloatSchema extends HaFormBaseSchema {
  type: "float";
}

export interface HaFormStringSchema extends HaFormBaseSchema {
  type: "string";
  format?: string;
}

export interface HaFormBooleanSchema extends HaFormBaseSchema {
  type: "boolean";
}

export interface HaFormTimeSchema extends HaFormBaseSchema {
  type: "positive_time_period_dict";
}



export type HaFormData =
  | HaFormStringData
  | HaFormIntegerData
  | HaFormFloatData
  | HaFormBooleanData
  | HaFormSelectData
  | HaFormMultiSelectData
  | HaFormTimeData;

export type HaFormStringData = string;
export type HaFormIntegerData = number;
export type HaFormFloatData = number;
export type HaFormBooleanData = boolean;
export type HaFormSelectData = string;
export type HaFormMultiSelectData = string[];
export type HaFormTimeData = HaTimeData;


export interface HaTimeData {
  hours?: number;
  minutes?: number;
  seconds?: number;
  milliseconds?: number;
}



export type HassService = {
  name?: string;
  description: string;
  target?: {} | null;
  fields: {
    [field_name: string]: {
      name?: string;
      description: string;
      example: string | boolean | number;
      selector?: {};
    };
  };
};


export type HassDomainServices = {
  [service_name: string]: HassService;
};

export type HassServices = {
  [domain: string]: HassDomainServices;
};


export function parseQuery<T>(queryString: string) {
  const query: any = {};
  const items = queryString.split("&");
  for (let i = 0; i < items.length; i++) {
    const item = items[i].split("=");
    const key = decodeURIComponent(item[0]);
    const value = item.length > 1 ? decodeURIComponent(item[1]) : undefined;
    query[key] = value;
  }
  return query as T;
}