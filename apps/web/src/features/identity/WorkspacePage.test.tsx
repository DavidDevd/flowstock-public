import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { changePassword } from "../../lib/auth";
import { WorkspacePage } from "./WorkspacePage";

vi.mock("../../lib/auth", () => ({
  changePassword: vi.fn().mockResolvedValue(undefined),
  listUsers: vi.fn().mockResolvedValue([]),
}));

describe("WorkspacePage", () => {
  it("shows identity state and logs out", () => {
    const leave = vi.fn();
    render(
      <WorkspacePage
        onLogout={leave}
        user={{
          id: "1",
          email: "admin@example.com",
          name: "Admin FlowStock",
          role: "administrator",
          permissions: ["users.manage"],
          must_change_password: true,
          active: true,
        }}
      />,
    );
    expect(screen.getAllByText("Administrador").length).toBeGreaterThanOrEqual(
      2,
    );
    expect(screen.getByText(/senha temporária/i)).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Senha atual"), {
      target: { value: "temporary password" },
    });
    fireEvent.change(screen.getByLabelText("Nova senha"), {
      target: { value: "replacement password" },
    });
    fireEvent.submit(
      screen
        .getByRole("button", { name: "Salvar nova senha" })
        .closest("form")!,
    );
    expect(changePassword).toHaveBeenCalledWith(
      "temporary password",
      "replacement password",
    );
    fireEvent.click(screen.getByRole("button", { name: "Sair" }));
    expect(leave).toHaveBeenCalledOnce();
  });

  it("falls back to an unknown role label without a password notice", () => {
    render(
      <WorkspacePage
        onLogout={vi.fn()}
        user={{
          id: "2",
          email: "custom@example.com",
          name: "Custom",
          role: "custom",
          permissions: [],
          must_change_password: false,
          active: true,
        }}
      />,
    );
    expect(screen.getAllByText("custom")).toHaveLength(2);
    expect(screen.queryByText(/senha temporária/i)).not.toBeInTheDocument();
  });
});
