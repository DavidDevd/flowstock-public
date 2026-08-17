import { afterEach, describe, expect, it, vi } from "vitest";

import {
  changePassword,
  completeRecovery,
  createUser,
  getSession,
  initiateRecovery,
  listUsers,
  login,
  logout,
  updateUser,
} from "./auth";

afterEach(() => vi.unstubAllGlobals());

describe("identity API", () => {
  it("logs in and forwards CSRF on logout", async () => {
    const user = {
      id: "1",
      email: "admin@example.com",
      name: "Admin",
      role: "administrator",
      permissions: ["users.manage"],
      must_change_password: false,
      active: true,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ user, csrf_token: "csrf" }), {
          status: 200,
        }),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(login(user.email, "secure password")).resolves.toEqual(user);
    await logout();
    const logoutInit = fetchMock.mock.calls[1]?.[1] as RequestInit;
    expect(new Headers(logoutInit.headers).get("X-CSRF-Token")).toBe("csrf");
  });

  it("reports authentication failure safely", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response("{}", { status: 401 })),
    );
    await expect(getSession()).rejects.toThrow("Credenciais inválidas.");
  });

  it("changes the password through a protected request", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(new Response(null, { status: 204 })),
    );
    await changePassword("current password", "replacement password");
    expect(fetch).toHaveBeenCalled();
  });

  it("supports the complete user administration API", async () => {
    const user = {
      id: "1",
      email: "operator@example.com",
      name: "Operator",
      role: "cashier",
      permissions: [],
      must_change_password: false,
      active: true,
    };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify([user]), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(user), { status: 201 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(user), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            credential: "credential",
            expires_in_seconds: 1800,
          }),
          {
            status: 200,
          },
        ),
      )
      .mockResolvedValueOnce(new Response(null, { status: 204 }));
    vi.stubGlobal("fetch", fetchMock);

    await expect(listUsers()).resolves.toEqual([user]);
    await createUser({
      email: user.email,
      name: user.name,
      role: user.role,
      temporary_password: "temporary password",
      current_password: "administrator password",
    });
    await updateUser(user.id, {
      active: false,
      current_password: "administrator password",
    });
    await initiateRecovery(user.id, "administrator password");
    await completeRecovery(user.email, "credential", "replacement password");
    expect(fetchMock).toHaveBeenCalledTimes(5);
  });
});
