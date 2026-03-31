import { act, renderHook } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { useDebounce } from "./useDebounce";

describe("useDebounce", () => {
  beforeEach(() => {
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it("returns the initial value immediately", () => {
    const { result } = renderHook(() => useDebounce("hello"));
    expect(result.current).toBe("hello");
  });

  it("does not update the value before the delay elapses", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      {
        initialProps: { value: "initial" },
      },
    );

    rerender({ value: "updated" });
    act(() => vi.advanceTimersByTime(100));

    expect(result.current).toBe("initial");
  });

  it("updates the value after the delay elapses", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      {
        initialProps: { value: "initial" },
      },
    );

    rerender({ value: "updated" });
    act(() => vi.advanceTimersByTime(300));

    expect(result.current).toBe("updated");
  });

  it("uses 500ms default delay", () => {
    const { result, rerender } = renderHook(({ value }) => useDebounce(value), {
      initialProps: { value: "a" },
    });

    rerender({ value: "b" });
    act(() => vi.advanceTimersByTime(499));
    expect(result.current).toBe("a");

    act(() => vi.advanceTimersByTime(1));
    expect(result.current).toBe("b");
  });

  it("resets the timer when value changes before delay elapses", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 300),
      {
        initialProps: { value: "a" },
      },
    );

    rerender({ value: "b" });
    act(() => vi.advanceTimersByTime(200));
    rerender({ value: "c" });
    act(() => vi.advanceTimersByTime(200));
    expect(result.current).toBe("a"); // still not past 300ms from last change

    act(() => vi.advanceTimersByTime(100));
    expect(result.current).toBe("c");
  });

  it("works with non-string types", () => {
    const { result, rerender } = renderHook(
      ({ value }) => useDebounce(value, 200),
      {
        initialProps: { value: 1 },
      },
    );

    rerender({ value: 99 });
    act(() => vi.advanceTimersByTime(200));
    expect(result.current).toBe(99);
  });
});
