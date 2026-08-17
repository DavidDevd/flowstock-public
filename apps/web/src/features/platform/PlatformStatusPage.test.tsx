import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { AppProviders } from "../../app/providers";
import { fetchReadiness } from "../../lib/api";
import { PlatformStatusPage } from "./PlatformStatusPage";

vi.mock("../../lib/api", () => ({
  fetchReadiness: vi.fn(),
}));

const mockedFetchReadiness = vi.mocked(fetchReadiness);

function renderPage() {
  return render(
    <AppProviders>
      <PlatformStatusPage />
    </AppProviders>,
  );
}

describe("PlatformStatusPage", () => {
  it("reports the foundation as operational when readiness passes", async () => {
    mockedFetchReadiness.mockResolvedValue({
      status: "ok",
      checks: {
        database: "ok",
      },
    });

    renderPage();

    expect(await screen.findByText("Operacional")).toBeInTheDocument();
    expect(
      screen.getByText("Fundação pronta para evoluir"),
    ).toBeInTheDocument();
  });

  it("shows a safe diagnostic state when readiness fails", async () => {
    mockedFetchReadiness.mockRejectedValue(new Error("database unavailable"));

    renderPage();

    expect(
      await screen.findByText("Indisponível", {}, { timeout: 3_000 }),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/identificador de correlação dos logs/i),
    ).toBeInTheDocument();
    expect(screen.queryByText(/database unavailable/i)).not.toBeInTheDocument();
  });
});
