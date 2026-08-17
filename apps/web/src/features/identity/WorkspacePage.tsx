import { useState, type FormEvent } from "react";

import { changePassword, type AuthenticatedUser } from "../../lib/auth";
import { UserManagement } from "./UserManagement";
import { MasterDataPanel } from "../masterData/MasterDataPanel";

const roleLabels: Record<string, string> = {
  administrator: "Administrador",
  manager: "Gerente",
  cashier: "Operador",
};

export function WorkspacePage({
  user,
  onLogout,
}: {
  user: AuthenticatedUser;
  onLogout: () => void;
}) {
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordChanged, setPasswordChanged] = useState(false);

  async function submitPassword(event: FormEvent) {
    event.preventDefault();
    await changePassword(currentPassword, newPassword);
    setPasswordChanged(true);
  }

  return (
    <section className="workspace">
      <aside className="workspace-nav">
        <p className="eyebrow">FlowStock</p>
        <strong>{user.name}</strong>
        <span>{roleLabels[user.role] ?? user.role}</span>
        <nav aria-label="Navegação principal">
          <a aria-current="page" href="/">
            Visão geral
          </a>
        </nav>
        <button className="button-secondary" onClick={onLogout} type="button">
          Sair
        </button>
      </aside>
      <div className="workspace-content">
        <p className="eyebrow">Sprint 1 · Identidade</p>
        <h2>Olá, {user.name.split(" ")[0]}.</h2>
        <p>Sua sessão está protegida e pronta para os módulos operacionais.</p>
        {user.must_change_password && !passwordChanged ? (
          <form
            className="notice password-form"
            onSubmit={(event) => void submitPassword(event)}
          >
            <strong>Altere sua senha temporária</strong>
            <input
              aria-label="Senha atual"
              onChange={(event) => setCurrentPassword(event.target.value)}
              required
              type="password"
            />
            <input
              aria-label="Nova senha"
              minLength={12}
              onChange={(event) => setNewPassword(event.target.value)}
              required
              type="password"
            />
            <button type="submit">Salvar nova senha</button>
          </form>
        ) : null}
        <div className="summary-grid">
          <article>
            <span>Sessão</span>
            <strong>Ativa</strong>
          </article>
          <article>
            <span>Perfil</span>
            <strong>{roleLabels[user.role] ?? user.role}</strong>
          </article>
          <article>
            <span>Permissões</span>
            <strong>{user.permissions.length}</strong>
          </article>
        </div>
        {user.permissions.includes("users.manage") ? (
          <UserManagement currentUserId={user.id} />
        ) : null}
        {user.permissions.includes("catalog.manage") ||
        user.permissions.includes("customers.manage") ? (
          <MasterDataPanel user={user} />
        ) : null}
      </div>
    </section>
  );
}
