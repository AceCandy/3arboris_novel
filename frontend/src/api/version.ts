import { API_BASE_URL } from './admin';

const configuredVersionCheckUrl = String(import.meta.env.VITE_VERSION_CHECK_URL || '').trim();
const defaultVersionCheckUrl = `${API_BASE_URL}/api/updates/remote-version`;

const normalizeVersion = (rawVersion: string): string => rawVersion.trim().replace(/^v(?=\d)/i, '');

const isLikelyVersion = (rawValue: string): boolean => (
  rawValue.length > 0
  && rawValue.length <= 64
  && !/[<>\s]/.test(rawValue)
  && /^[\w.+-]+$/.test(rawValue)
);

const pickVersionFromPayload = (payload: unknown): string | null => {
  if (typeof payload === 'string') {
    const normalized = normalizeVersion(payload);
    return isLikelyVersion(normalized) ? normalized : null;
  }

  if (!payload || typeof payload !== 'object') {
    return null;
  }

  const payloadRecord = payload as Record<string, unknown>;
  const candidateKeys = ['version', 'latest_version', 'tag_name', 'app_version'] as const;
  for (const key of candidateKeys) {
    const candidate = payloadRecord[key];
    if (typeof candidate === 'string' && candidate.trim()) {
      const normalized = normalizeVersion(candidate);
      if (isLikelyVersion(normalized)) {
        return normalized;
      }
    }
  }

  return null;
};

export const getRemoteVersion = async (): Promise<string | null> => {
  const url = configuredVersionCheckUrl || defaultVersionCheckUrl;
  const response = await fetch(url, { method: 'GET' });
  if (!response.ok) {
    throw new Error(`Version check failed, status code: ${response.status}`);
  }

  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    const payload = await response.json();
    return pickVersionFromPayload(payload);
  }

  const text = await response.text();
  return pickVersionFromPayload(text);
};

export const normalizeComparableVersion = (rawVersion: string): string =>
  normalizeVersion(rawVersion);
