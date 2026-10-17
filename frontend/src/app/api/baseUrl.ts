const API_BASE_ENV_KEY = 'VITE_API_BASE_URL';

function resolveApiBaseUrl(): string | null {
  const rawBaseUrl = import.meta.env[API_BASE_ENV_KEY]?.trim();

  if (!rawBaseUrl) {
    return null;
  }

  try {
    return new URL(rawBaseUrl).toString();
  } catch {
    return null;
  }
}

function resolveRelativeApiPath(path: string): string {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`;

  if (!import.meta.env.PROD || import.meta.env.BASE_URL === '/') {
    return normalizedPath;
  }

  const normalizedBase = import.meta.env.BASE_URL.replace(/\/$/, '');
  return `${normalizedBase}${normalizedPath}`;
}

export function resolveApiPath(path: string): string {
  const baseUrl = resolveApiBaseUrl();

  if (!baseUrl) {
    return resolveRelativeApiPath(path);
  }

  return new URL(path, baseUrl).toString();
}

export { resolveApiBaseUrl };
