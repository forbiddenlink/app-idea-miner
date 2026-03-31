import { describe, expect, it } from "vitest";
import { cn } from "./cn";

describe("cn", () => {
  it("returns a string for a single class", () => {
    expect(cn("foo")).toBe("foo");
  });

  it("merges multiple classes", () => {
    expect(cn("foo", "bar")).toBe("foo bar");
  });

  it("ignores falsy values", () => {
    expect(cn("foo", false, undefined, null, "", "bar")).toBe("foo bar");
  });

  it("resolves Tailwind conflicts — last wins", () => {
    expect(cn("p-4", "p-2")).toBe("p-2");
    expect(cn("text-red-500", "text-blue-500")).toBe("text-blue-500");
  });

  it("supports conditional classes via object syntax", () => {
    expect(cn({ "font-bold": true, italic: false })).toBe("font-bold");
  });

  it("returns empty string with no arguments", () => {
    expect(cn()).toBe("");
  });
});
