import { afterEach, describe, expect, it, vi } from "vitest";

import { fetchReadiness } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});

describe("fetchReadiness", () => {
  it("returns the safe readiness contract", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(
        JSON.stringify({
          status: "ok",
          checks: {
            database: "ok",
          },
        }),
        {
          status: 200,
          headers: {
            "Content-Type": "application/json",
          },
        },
      ),
    );
    vi.stubGlobal("fetch", fetchMock);

    await expect(fetchReadiness()).resolves.toEqual({
      status: "ok",
      checks: {
        database: "ok",
      },
    });
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/health/ready",
      expect.objectContaining({
        credentials: "same-origin",
        signal: null,
      }),
    );
  });

  it("rejects a non-ready response without exposing its body", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response("database host is sensitive", {
          status: 503,
        }),
      ),
    );

    await expect(fetchReadiness(new AbortController().signal)).rejects.toThrow(
      "FlowStock platform is not ready.",
    );
  });
});
