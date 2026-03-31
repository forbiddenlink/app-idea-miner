import { renderHook } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

// Mock useNavigate so we can assert navigate calls without a real router history
const mockNavigate = vi.fn();
vi.mock("react-router-dom", async (importOriginal) => {
  const actual = await importOriginal<typeof import("react-router-dom")>();
  return { ...actual, useNavigate: () => mockNavigate };
});

import { useKeyboardShortcuts } from "./useKeyboardShortcuts";

function wrapper({ children }: { children: React.ReactNode }) {
  return <MemoryRouter>{children}</MemoryRouter>;
}

function fireKey(
  key: string,
  mods: { ctrlKey?: boolean; shiftKey?: boolean; altKey?: boolean } = {},
) {
  document.dispatchEvent(
    new KeyboardEvent("keydown", {
      key,
      bubbles: true,
      ctrlKey: mods.ctrlKey ?? false,
      shiftKey: mods.shiftKey ?? false,
      altKey: mods.altKey ?? false,
    }),
  );
}

describe("useKeyboardShortcuts", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
    renderHook(() => useKeyboardShortcuts(), { wrapper });
  });

  afterEach(() => {
    // Clean up listener by unmounting — handled by renderHook
  });

  it("Alt+H navigates to /", () => {
    fireKey("h", { altKey: true });
    expect(mockNavigate).toHaveBeenCalledWith("/");
  });

  it("Alt+C navigates to /clusters", () => {
    fireKey("c", { altKey: true });
    expect(mockNavigate).toHaveBeenCalledWith("/clusters");
  });

  it("Alt+A navigates to /analytics", () => {
    fireKey("a", { altKey: true });
    expect(mockNavigate).toHaveBeenCalledWith("/analytics");
  });

  it("Ctrl+K dispatches app:command-palette-open event", () => {
    const listener = vi.fn();
    globalThis.addEventListener("app:command-palette-open", listener);
    fireKey("k", { ctrlKey: true });
    expect(listener).toHaveBeenCalledOnce();
    globalThis.removeEventListener("app:command-palette-open", listener);
  });

  it("Shift+? dispatches app:keyboard-shortcuts-open event", () => {
    const listener = vi.fn();
    globalThis.addEventListener("app:keyboard-shortcuts-open", listener);
    fireKey("?", { shiftKey: true });
    expect(listener).toHaveBeenCalledOnce();
    globalThis.removeEventListener("app:keyboard-shortcuts-open", listener);
  });

  it("does not fire shortcuts when user is typing in an input", () => {
    const input = document.createElement("input");
    document.body.appendChild(input);
    input.focus();

    input.dispatchEvent(
      new KeyboardEvent("keydown", { key: "h", altKey: true, bubbles: true }),
    );
    expect(mockNavigate).not.toHaveBeenCalled();

    input.remove();
  });

  it("does not navigate for unregistered keys", () => {
    fireKey("z");
    expect(mockNavigate).not.toHaveBeenCalled();
  });
});
