import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("renders the MVP shell and its child route", () => {
    render(
      <App>
        <p>Conteúdo da operação</p>
      </App>,
    );
    expect(
      screen.getByRole("heading", { name: "FlowStock" }),
    ).toBeInTheDocument();
    expect(screen.getByText("MVP")).toBeInTheDocument();
    expect(screen.getByText("Conteúdo da operação")).toBeInTheDocument();
    expect(
      screen.getByText(/Operação simples, segura e rastreável/i),
    ).toBeInTheDocument();
  });
});
