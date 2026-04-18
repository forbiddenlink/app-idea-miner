import { render } from "@/test/utils";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it } from "vitest";
import Settings, { useRefreshSettings } from "./Settings";

// ---------------------------------------------------------------------------
// Settings page
// ---------------------------------------------------------------------------
describe("Settings", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("renders the page heading", () => {
    render(<Settings />);
    expect(
      screen.getByRole("heading", { name: /^settings$/i, level: 1 }),
    ).toBeInTheDocument();
  });

  it("renders the auto-refresh toggle as a checkbox", () => {
    render(<Settings />);
    expect(
      screen.getByRole("checkbox", { name: /auto-refresh/i }),
    ).toBeInTheDocument();
  });

  it("renders the refresh interval select", () => {
    render(<Settings />);
    expect(
      screen.getByRole("combobox", { name: /refresh interval/i }),
    ).toBeInTheDocument();
  });

  it("shows all four data source names", () => {
    render(<Settings />);
    expect(screen.getByText("RSS Feeds")).toBeInTheDocument();
    expect(screen.getByText("Reddit")).toBeInTheDocument();
    expect(screen.getByText("ProductHunt")).toBeInTheDocument();
    expect(screen.getByText("HackerNews")).toBeInTheDocument();
  });

  it("toggle is on by default when localStorage is empty", () => {
    render(<Settings />);
    const toggle = screen.getByRole("checkbox", { name: /auto-refresh/i });
    expect(toggle).toBeChecked();
  });

  it("clicking the toggle writes false to localStorage", async () => {
    render(<Settings />);
    const toggle = screen.getByRole("checkbox", { name: /auto-refresh/i });
    await userEvent.click(toggle);
    expect(window.localStorage.getItem("aim_auto_refresh")).toBe("false");
  });

  it("toggle reflects false when localStorage is pre-set to false", () => {
    window.localStorage.setItem("aim_auto_refresh", "false");
    render(<Settings />);
    const toggle = screen.getByRole("checkbox", { name: /auto-refresh/i });
    expect(toggle).not.toBeChecked();
  });
});

// ---------------------------------------------------------------------------
// useRefreshSettings hook
// ---------------------------------------------------------------------------
describe("useRefreshSettings", () => {
  beforeEach(() => {
    window.localStorage.clear();
  });

  it("returns enabled:true and interval:60000 when localStorage is empty", () => {
    const { enabled, interval } = useRefreshSettings();
    expect(enabled).toBe(true);
    expect(interval).toBe(60000);
  });

  it("reads aim_auto_refresh=false from localStorage", () => {
    window.localStorage.setItem("aim_auto_refresh", "false");
    const { enabled } = useRefreshSettings();
    expect(enabled).toBe(false);
  });

  it("reads a custom interval from localStorage", () => {
    window.localStorage.setItem("aim_refresh_interval", "30000");
    const { interval } = useRefreshSettings();
    expect(interval).toBe(30000);
  });
});
