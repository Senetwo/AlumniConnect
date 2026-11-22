
const TOKEN_KEY = "alumniconnect_token";
const USER_KEY = "alumniconnect_user";
let tokenProvider = null;
let signOutProvider = null;
let inMemoryToken = null;
let inMemoryUser = null;

export function setClerkSession(getToken, signOut) {
  tokenProvider = getToken;
  signOutProvider = signOut;
}

export async function getRequestToken() {
  const auth = getAuth();
  // Prefer an explicitly saved AlumniConnect password session. When the
  // current user signed in through Clerk, refresh that short-lived token.
  if (auth && !auth.clerk) return auth.token;
  if (auth?.clerk && tokenProvider) {
    const token = await tokenProvider();
    if (token) return token;
  }
  if (tokenProvider) {
    const token = await tokenProvider();
    if (token) return token;
  }
  return auth?.token || null;
}

export async function signOutCurrentUser() {
  try {
    if (signOutProvider) await signOutProvider();
  } finally {
    clearAuth();
  }
}

export function getAuth() {
  if (inMemoryToken && inMemoryUser) {
    return { token: inMemoryToken, user: inMemoryUser, storage: sessionStorage, clerk: true };
  }
  for (const storage of [localStorage, sessionStorage]) {
    const token = storage.getItem(TOKEN_KEY);
    const storedUser = storage.getItem(USER_KEY);

    if (!token || !storedUser) continue;

    try {
      return {
        token,
        user: JSON.parse(storedUser),
        storage,
      };
    } catch {
      storage.removeItem(TOKEN_KEY);
      storage.removeItem(USER_KEY);
    }
  }

  return null;
}

export function saveClerkAuth(token, user) {
  clearAuth();
  inMemoryToken = token;
  inMemoryUser = user;
  sessionStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function saveAuth(token, user, rememberMe = false) {
  clearAuth();

  const storage = rememberMe ? localStorage : sessionStorage;
  storage.setItem(TOKEN_KEY, token);
  storage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearAuth() {
  inMemoryToken = null;
  inMemoryUser = null;
  for (const storage of [localStorage, sessionStorage]) {
    storage.removeItem(TOKEN_KEY);
    storage.removeItem(USER_KEY);
  }
}
