/**
 * Resolves avatar URL regardless of whether the backend stored
 * a full URL (old behaviour) or a relative path (new behaviour).
 * Also appends a cache-busting timestamp.
 */
export function resolveAvatarUrl(
  url: string | null | undefined,
  apiBase: string,
  ts?: number,
): string | null {
  if (!url) return null
  let resolved: string
  if (url.startsWith('http://') || url.startsWith('https://')) {
    // Full URL stored by old backend — replace origin with current apiBase
    try {
      const u = new URL(url)
      const base = new URL(apiBase)
      resolved = `${base.origin}${u.pathname}`
    } catch {
      resolved = url
    }
  } else {
    // Relative path stored by new backend
    resolved = `${apiBase}${url}`
  }
  return ts ? `${resolved}?t=${ts}` : resolved
}
