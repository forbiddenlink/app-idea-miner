/**
 * The browser bundle must never carry an API key: any VITE_ variable is
 * inlined into public JS. The server attaches X-API-Key itself
 * (apps/api/app/core/browser_key.py).
 */
import { describe, expect, it } from "vitest";
import { readFileSync } from "node:fs";
import { resolve } from "node:path";

const source = readFileSync(resolve(__dirname, "api.ts"), "utf8");

describe("api client key handling", () => {
  it("does not read VITE_API_KEY", () => {
    expect(source).not.toMatch(/VITE_API_KEY/);
  });

  it("has no dev-api-key fallback", () => {
    expect(source).not.toMatch(/dev-api-key/);
  });

  it("does not set an X-API-Key header", () => {
    expect(source).not.toMatch(/X-API-Key/i);
  });
});
