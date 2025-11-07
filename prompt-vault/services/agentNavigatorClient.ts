/**
 * Helper utilities for calling the Agent Navigator backend using
 * Workload Identity authentication from Cloud Run.
 */

const METADATA_URL =
  'http://metadata/computeMetadata/v1/instance/service-accounts/default/identity';

let cachedToken: string | null = null;
let cachedExpiration = 0;

const TOKEN_TTL_MS = 55 * 60 * 1000; // 55 minutes

async function fetchIdToken(audience: string): Promise<string> {
  const now = Date.now();
  if (cachedToken && cachedExpiration > now) {
    return cachedToken;
  }

  const response = await fetch(
    `${METADATA_URL}?audience=${encodeURIComponent(audience)}`,
    {
      headers: {
        'Metadata-Flavor': 'Google',
      },
    }
  );

  if (!response.ok) {
    throw new Error(`Failed to fetch ID token: ${response.status} ${response.statusText}`);
  }

  const token = await response.text();
  cachedToken = token;
  cachedExpiration = now + TOKEN_TTL_MS;
  return token;
}

export interface CallOptions extends RequestInit {
  expectedAudience?: string;
}

export async function callAgentNavigator(
  url: string,
  options: CallOptions = {}
): Promise<Response> {
  const audience =
    options.expectedAudience || process.env.EXPECTED_AUDIENCE || url.split('?')[0];
  const idToken = await fetchIdToken(audience);

  const headers = new Headers(options.headers);
  headers.set('Authorization', `Bearer ${idToken}`);

  return fetch(url, {
    ...options,
    headers,
  });
}

export function resetTokenCache(): void {
  cachedToken = null;
  cachedExpiration = 0;
}

