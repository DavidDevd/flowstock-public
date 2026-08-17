import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import {
  createUser,
  initiateRecovery,
  listUsers,
  updateUser,
} from "../../lib/auth";
import { UserManagement } from "./UserManagement";

vi.mock("../../lib/auth", () => ({
  createUser: vi.fn(),
  initiateRecovery: vi.fn(),
  listUsers: vi.fn(),
  updateUser: vi.fn(),
}));

const user = {
  id: "user-1",
  email: "operator@example.com",
  name: "Operator",
  role: "cashier",
  permissions: [],
  must_change_password: false,
  active: true,
};

describe("UserManagement", () => {
  it("creates, updates, deactivates and starts recovery", async () => {
    vi.mocked(listUsers).mockResolvedValue([user]);
    vi.mocked(createUser).mockResolvedValue(user);
    vi.mocked(updateUser).mockResolvedValue(user);
    vi.mocked(initiateRecovery).mockResolvedValue({
      credential: "one-time-recovery-credential",
      expires_in_seconds: 1800,
    });
    render(<UserManagement currentUserId="admin-1" />);
    expect(await screen.findByText(user.email)).toBeInTheDocument();

    fireEvent.change(screen.getByLabelText("Senha do administrador"), {
      target: { value: "administrator password" },
    });
    fireEvent.change(screen.getByLabelText("Nome do novo usuário"), {
      target: { value: "New User" },
    });
    fireEvent.change(screen.getByLabelText("E-mail do novo usuário"), {
      target: { value: "new@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Senha temporária"), {
      target: { value: "temporary password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Adicionar usuário" }));
    await waitFor(() => expect(createUser).toHaveBeenCalled());

    fireEvent.change(screen.getByLabelText(`Nome de ${user.email}`), {
      target: { value: "Updated Operator" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Salvar" }));
    await waitFor(() => expect(updateUser).toHaveBeenCalled());

    fireEvent.click(screen.getByRole("button", { name: "Desativar" }));
    fireEvent.click(screen.getByRole("button", { name: "Recuperar senha" }));
    expect(
      await screen.findByText("one-time-recovery-credential"),
    ).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Já copiei" }));
    expect(
      screen.queryByText("one-time-recovery-credential"),
    ).not.toBeInTheDocument();
  });

  it("shows a safe loading failure", async () => {
    vi.mocked(listUsers).mockRejectedValue(new Error("sensitive"));
    render(<UserManagement currentUserId="admin-1" />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Não foi possível carregar os usuários.",
    );
  });
});
