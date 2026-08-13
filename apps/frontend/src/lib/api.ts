import { useAuthStore } from '../store/authStore';

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || 'https://rail-yatra-backend.onrender.com';

interface RefreshResponse {
  success?: boolean;
  data?: {
    accessToken?: string;
  };
}

/**
 * Authenticated fetch for browser API calls.
 * Sends the refresh cookie cross-site and retries one time after a 401.
 */
export async function authenticatedFetch(
  input: RequestInfo | URL,
  init: RequestInit = {},
): Promise<Response> {
  const makeRequest = (accessToken: string | null) => {
    const headers = new Headers(init.headers);
    if (accessToken) headers.set('Authorization', `Bearer ${accessToken}`);
    return fetch(input, {
      ...init,
      headers,
      credentials: 'include',
    });
  };

  const { token, setAuth, user, clearAuth } = useAuthStore.getState();
  let response = await makeRequest(token);

  if (response.status !== 401) return response;

  // Never recursively refresh the refresh endpoint itself.
  const url = typeof input === 'string' ? input : input.toString();
  if (url.endsWith('/auth/refresh')) {
    clearAuth();
    return response;
  }

  try {
    const refreshResponse = await fetch(`${API_BASE_URL}/api/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
    });

    if (!refreshResponse.ok) {
      clearAuth();
      return response;
    }

    const refreshData = (await refreshResponse.json()) as RefreshResponse;
    const refreshedToken = refreshData.data?.accessToken;
    if (!refreshedToken || !user) {
      clearAuth();
      return response;
    }

    setAuth(refreshedToken, user);
    response = await makeRequest(refreshedToken);
  } catch (error) {
    console.error('Session refresh failed:', error);
  }

  return response;
}
