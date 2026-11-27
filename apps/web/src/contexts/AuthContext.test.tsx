import { render, screen, waitFor } from "@testing-library/react";
import axios from "axios";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { AuthProvider, useAuth } from "./AuthContext";

vi.mock("axios", async (importOriginal) => {
  const actual = await importOriginal<typeof import("axios")>();
  return {
    ...actual,
    default: { ...actual.default, get: vi.fn(), post: vi.fn() },
  };
});

function Probe() {
  const { isLoading, isAuthenticated, user } = useAuth();
  return (
    <div>
      <span data-testid="loading">{String(isLoading)}</span>
      <span data-testid="authed">{String(isAuthenticated)}</span>
      <span data-testid="email">{user?.email ?? ""}</span>
    </div>
  );
}

function clearCsrfCookie() {
  document.cookie = "aim_csrf_token=; max-age=0; path=/";
}

describe("AuthProvider session check", () => {
  beforeEach(() => {
    vi.mocked(axios.get).mockReset();
    clearCsrfCookie();
  });
  afterEach(clearCsrfCookie);

  it("does not call /auth/me for anonymous visitors", async () => {
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(axios.get).not.toHaveBeenCalled();
    expect(screen.getByTestId("authed").textContent).toBe("false");
  });

  it("calls /auth/me once when a session hint exists", async () => {
    document.cookie = "aim_csrf_token=abc; path=/";
    vi.mocked(axios.get).mockResolvedValue({
      data: { id: "1", email: "a@example.com", is_active: true, is_admin: false },
    });
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() =>
      expect(screen.getByTestId("email").textContent).toBe("a@example.com"),
    );
    expect(axios.get).toHaveBeenCalledTimes(1);
  });

  it("treats a 401 as logged out", async () => {
    document.cookie = "aim_csrf_token=abc; path=/";
    vi.mocked(axios.get).mockRejectedValue(new Error("401"));
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    await waitFor(() =>
      expect(screen.getByTestId("loading").textContent).toBe("false"),
    );
    expect(screen.getByTestId("authed").textContent).toBe("false");
  });
});
