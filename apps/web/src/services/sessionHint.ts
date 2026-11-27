export const CSRF_COOKIE_NAME = "aim_csrf_token";

/** Reads the non-httpOnly double-submit CSRF cookie, if present. */
export function readCsrfCookie(): string | null {
  if (globalThis.document === undefined) return null;
  const match = globalThis.document.cookie
    .split("; ")
    .find((row) => row.startsWith(`${CSRF_COOKIE_NAME}=`));
  return match ? decodeURIComponent(match.split("=")[1]) : null;
}

/**
 * The session cookie is httpOnly, so JS cannot see it. The CSRF cookie is set
 * and cleared together with it (same path and lifetime), which makes it a
 * reliable "a session probably exists" hint. Anonymous visitors have neither.
 */
export function hasSessionHint(): boolean {
  return readCsrfCookie() !== null;
}
