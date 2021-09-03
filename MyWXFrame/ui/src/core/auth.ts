
import { AuthData, QueryCallbackData, AuthorizationCodeRequest, RefreshTokenRequest, parseQuery } from "./type";


const storage = window.localStorage || {};

declare global {
  interface Window {
    __tokenCache: {
      // undefined: we haven't loaded yet
      // null: none stored
      tokens?: AuthData | null;
      writeEnabled?: boolean;
    };
  }
}

// So that core.js and main app hit same shared object.
let tokenCache = window.__tokenCache;
if (!tokenCache) {
  tokenCache = window.__tokenCache = {
    tokens: undefined,
    writeEnabled: undefined,
  };
}

export function askWrite() {
  return (
    tokenCache.tokens !== undefined && tokenCache.writeEnabled === undefined
  );
}

export function saveTokens(tokens: AuthData | null) {
  tokenCache.tokens = tokens;
  if (tokenCache.writeEnabled) {
    try {
      storage.hassTokens = JSON.stringify(tokens);
    } catch (err) {
      // write failed, ignore it. Happens if storage is full or private mode.
    }
  }
}

export function enableWrite() {
  tokenCache.writeEnabled = true;
  if (tokenCache.tokens) {
    saveTokens(tokenCache.tokens);
  }
}

export function loadTokens() {
  if (tokenCache.tokens === undefined) {
    try {
      // Delete the old token cache.
      delete storage.tokens;
      const tokens = storage.hassTokens;
      if (tokens) {
        tokenCache.tokens = JSON.parse(tokens);
        tokenCache.writeEnabled = true;
      } else {
        tokenCache.tokens = null;
      }
    } catch (err) {
      tokenCache.tokens = null;
    }
  }
  return tokenCache.tokens;
}

export function clearTokens() {
  if (storage.clear) {
    storage.clear();
  }
}



export const genClientId = (): string =>
  `${location.protocol}//${location.host}/`;

export const genExpires = (expires_in: number): number => {
  return expires_in * 1000 + Date.now();
};

function genRedirectUrl() {
  // Get current url but without # part.
  const { protocol, host, pathname, search } = location;
  return `${protocol}//${host}${pathname}${search}`;
}

export const ERR_CANNOT_CONNECT = 1;
export const ERR_INVALID_AUTH = 2;
export const ERR_CONNECTION_LOST = 3;
export const ERR_HASS_HOST_REQUIRED = 4;
export const ERR_INVALID_HTTPS_TO_HTTP = 5;


async function tokenRequest(
  hassUrl: string,
  clientId: string | null,
  data: AuthorizationCodeRequest | RefreshTokenRequest
) {
  // Browsers don't allow fetching tokens from https -> http.
  // Throw an error because it's a pain to debug this.
  // Guard against not working in node.
  const l = typeof location !== "undefined" && location;
  if (l && l.protocol === "https:") {
    // Ensure that the hassUrl is hosted on https.
    const a = document.createElement("a");
    a.href = hassUrl;
    if (a.protocol === "http:" && a.hostname !== "localhost") {
      throw ERR_INVALID_HTTPS_TO_HTTP;
    }
  }

  const formData = new FormData();
  if (clientId !== null) {
    formData.append("client_id", clientId);
  }
  Object.keys(data).forEach((key) => {
    // @ts-ignore: Unreachable code error
    formData.append(key, data[key]);
  });


  const resp = await fetch(`${hassUrl}/auth/token`, {
    method: "POST",
    credentials: "same-origin",
    body: formData,
  });

  if (!resp.ok) {
    throw resp.status === 400 /* auth invalid */ ||
      resp.status === 403 /* user not active */
      ? ERR_INVALID_AUTH
      : new Error("Unable to fetch tokens");
  }

  const tokens: AuthData = await resp.json();
  tokens.hassUrl = hassUrl;
  tokens.clientId = clientId;
  tokens.expires = genExpires(tokens.expires_in);
  return tokens;
}

export function fetchToken(hassUrl: string, clientId: string | null, code: string) {
  return tokenRequest(hassUrl, clientId, {
    code,
    grant_type: "authorization_code",
  });
}


export type SaveTokensFunc = (data: AuthData | null) => void;
export type LoadTokensFunc = () => Promise<AuthData | null | undefined>;



export class Auth {
  private _saveTokens?: SaveTokensFunc;
  data: AuthData;

  constructor(data: AuthData, saveTokens?: SaveTokensFunc) {
    this.data = data;
    this._saveTokens = saveTokens;
  }

  get wsUrl() {
    // Convert from http:// -> ws://, https:// -> wss://
    return `ws${this.data.hassUrl.substr(4)}/api/websocket`;
  }

  get accessToken() {
    return this.data.access_token;
  }

  get expired() {
    return Date.now() > this.data.expires;
  }

  /**
   * Refresh the access token.
   */
  async refreshAccessToken() {
    if (!this.data.refresh_token) throw new Error("No refresh_token");

    const data = await tokenRequest(this.data.hassUrl, this.data.clientId, {
      grant_type: "refresh_token",
      refresh_token: this.data.refresh_token,
    });
    // Access token response does not contain refresh token.
    data.refresh_token = this.data.refresh_token;
    this.data = data;
    if (this._saveTokens) this._saveTokens(data);
  }

  /**
   * Revoke the refresh & access tokens.
   */
  async revoke() {
    if (!this.data.refresh_token) throw new Error("No refresh_token to revoke");

    const formData = new FormData();
    formData.append("action", "revoke");
    formData.append("token", this.data.refresh_token);

    // There is no error checking, as revoke will always return 200
    await fetch(`${this.data.hassUrl}/auth/token`, {
      method: "POST",
      credentials: "same-origin",
      body: formData,
    });

    if (this._saveTokens) {
      this._saveTokens(null);
    }
  }
}


export async function getAuth(hassurl: string): Promise<{ auth: Auth | null, hassUrl: string }> {
  let data: AuthData | null | undefined;

  const clientId = `${location.protocol}//${location.host}/`;

  //请求中带有auth_callback标识，需要到后台验证获取token
  const query = parseQuery<QueryCallbackData>(location.search.substr(1));
  if ("auth_callback" in query) {
    data = await fetchToken(hassurl, clientId, query.code);
    saveTokens(data);
  }

  // 读取存储的token
  if (!data) {
    data = await loadTokens();
  }

  if (data)
    return { auth: new Auth(data, saveTokens), hassUrl: hassurl }
  else
    return { auth: null, hassUrl: hassurl };
}