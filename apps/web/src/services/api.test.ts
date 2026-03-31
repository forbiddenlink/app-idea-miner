import { AxiosError, AxiosHeaders } from "axios";
import { describe, expect, it } from "vitest";
import { isRetryable } from "./api";

function makeAxiosError(status?: number, method = "get"): AxiosError {
  const err = new AxiosError("test error", undefined, {
    method,
    headers: new AxiosHeaders(),
  });
  if (status !== undefined) {
    err.response = {
      status,
      data: {},
      headers: {},
      statusText: String(status),
      // @ts-expect-error — minimal stub
      config: {},
    };
  }
  return err;
}

describe("isRetryable", () => {
  it("returns false for non-GET methods", () => {
    for (const method of ["post", "put", "patch", "delete"]) {
      expect(isRetryable(makeAxiosError(503, method), method)).toBe(false);
    }
  });

  it("returns true for network errors (no response)", () => {
    const err = makeAxiosError(undefined, "get");
    expect(isRetryable(err, "get")).toBe(true);
  });

  it("returns true for 429", () => {
    expect(isRetryable(makeAxiosError(429), "get")).toBe(true);
  });

  it("returns true for 502", () => {
    expect(isRetryable(makeAxiosError(502), "get")).toBe(true);
  });

  it("returns true for 503", () => {
    expect(isRetryable(makeAxiosError(503), "get")).toBe(true);
  });

  it("returns true for 504", () => {
    expect(isRetryable(makeAxiosError(504), "get")).toBe(true);
  });

  it("returns false for 404", () => {
    expect(isRetryable(makeAxiosError(404), "get")).toBe(false);
  });

  it("returns false for 500", () => {
    expect(isRetryable(makeAxiosError(500), "get")).toBe(false);
  });

  it("defaults method to GET when not provided", () => {
    // network error with no method supplied → should retry
    const err = makeAxiosError(undefined, "get");
    expect(isRetryable(err)).toBe(true);
  });
});
