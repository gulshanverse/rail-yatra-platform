import { useAuthStore } from '../store/authStore';

const configuredApiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

// Production must provide the backend explicitly. The Render URL is retained
// only as the current deployed default so existing Vercel deployments do not
// silently switch to a dead or unrelated service.
export const API_BASE_URL = configuredApiUrl || 'https://rail-yatra-backend.onrender.com';

export class ApiRequestError extends Error {
  readonly status: number;
  readonly code: string;

  constructor(message: string, status: number, code = 'API_REQUEST_FAILED') {
    super(message);
    this.name = 'ApiRequestError';
    this.status = status;
    this.code = code;
  }
}

export async function readApiError(response: Response): Promise<ApiRequestError> {
  let code = 'API_REQUEST_FAILED';
  let message = `Request failed (${response.status})`;

  try {
    const payload = (await response.json()) as {
      code?: string;
      message?: string;
      error?: string;
    };
    if (typeof payload.code === 'string') code = payload.code;
    if (typeof payload.message === 'string' && payload.message.trim()) {
      message = payload.message;
    } else if (typeof payload.error === 'string' && payload.error.trim()) {
      message = payload.error;
    }
  } catch {
    // Keep the status-derived message when the server did not return JSON.
  }

  return new ApiRequestError(message, response.status, code);
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

    const refreshData = (await refreshResponse.json()) as {
      success?: boolean;
      data?: { accessToken?: string };
    };
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
