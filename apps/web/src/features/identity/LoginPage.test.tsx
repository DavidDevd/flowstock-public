import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { completeRecovery, login } from "../../lib/auth";
import { LoginPage } from "./LoginPage";

vi.mock("../../lib/auth", () => ({
  completeRecovery: vi.fn(),
  login: vi.fn(),
}));
const mockedLogin = vi.mocked(login);

describe("LoginPage", () => {
  it("authenticates with the informed credentials", async () => {
    const user = {
      id: "1",
      email: "admin@example.com",
      name: "Admin",
      role: "administrator",
      permissions: [],
      must_change_password: false,
      active: true,
    };
    mockedLogin.mockResolvedValue(user);
    const authenticated = vi.fn();
    render(<LoginPage onAuthenticated={authenticated} />);

    fireEvent.change(screen.getByLabelText("E-mail"), {
      target: { value: user.email },
    });
    fireEvent.change(screen.getByLabelText("Senha"), {
      target: { value: "secure password" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: "Entrar" }).closest("form")!,
    );

    await waitFor(() => expect(authenticated).toHaveBeenCalledWith(user));
  });

  it("shows a safe error when authentication fails", async () => {
    mockedLogin.mockRejectedValue(new Error("Credenciais inválidas."));
    render(<LoginPage onAuthenticated={vi.fn()} />);
    fireEvent.change(screen.getByLabelText("E-mail"), {
      target: { value: "admin@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Senha"), {
      target: { value: "wrong" },
    });
    fireEvent.submit(
      screen.getByRole("button", { name: "Entrar" }).closest("form")!,
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Credenciais inválidas.",
    );
  });

  it("completes recovery with the one-time credential", async () => {
    vi.mocked(completeRecovery).mockResolvedValue(undefined);
    render(<LoginPage onAuthenticated={vi.fn()} />);
    fireEvent.click(
      screen.getByRole("button", { name: "Usar credencial de recuperação" }),
    );
    fireEvent.change(screen.getByLabelText("E-mail"), {
      target: { value: "operator@example.com" },
    });
    fireEvent.change(screen.getByLabelText("Credencial de recuperação"), {
      target: { value: "one-time-credential-value-with-enough-length" },
    });
    fireEvent.change(screen.getByLabelText("Nova senha"), {
      target: { value: "replacement password" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Definir nova senha" }));
    expect(await screen.findByText(/Senha alterada/i)).toBeInTheDocument();
  });
});
