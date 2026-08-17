import { afterEach, describe, expect, it, vi } from "vitest";

import {
  createMasterData,
  listMasterData,
  updateMasterData,
} from "./masterData";

afterEach(() => vi.unstubAllGlobals());

describe("master data API", () => {
  it("lists, creates and updates a resource", async () => {
    const page = { items: [], page: 2, size: 25, total: 0, pages: 1 };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(
        new Response(JSON.stringify(page), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "category-1" }), { status: 201 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify({ id: "category-1" }), { status: 200 }),
      );
    vi.stubGlobal("fetch", fetchMock);

    await expect(
      listMasterData("categories", "bebidas", 2, 25),
    ).resolves.toEqual(page);
    await createMasterData("categories", { name: "Bebidas" });
    await updateMasterData("categories", "category-1", { active: false });

    expect(fetchMock.mock.calls[0]?.[0]).toBe(
      "/api/v1/categories?search=bebidas&page=2&size=25",
    );
    expect(fetchMock.mock.calls[1]?.[1]).toMatchObject({ method: "POST" });
    expect(fetchMock.mock.calls[2]?.[1]).toMatchObject({ method: "PATCH" });
  });
});
