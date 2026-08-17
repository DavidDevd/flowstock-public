import { useEffect, useState, type FormEvent } from "react";

import {
  createUser,
  initiateRecovery,
  listUsers,
  updateUser,
  type AuthenticatedUser,
} from "../../lib/auth";

const emptyCreate = {
  email: "",
  name: "",
  role: "cashier",
  temporary_password: "",
};

export function UserManagement({ currentUserId }: { currentUserId: string }) {
  const [users, setUsers] = useState<AuthenticatedUser[]>([]);
  const [reauthentication, setReauthentication] = useState("");
  const [create, setCreate] = useState(emptyCreate);
  const [error, setError] = useState("");
  const [recoveryCredential, setRecoveryCredential] = useState("");

  async function refresh() {
    setUsers(await listUsers());
  }

  useEffect(() => {
    void listUsers()
      .then(setUsers)
      .catch(() => setError("Não foi possível carregar os usuários."));
  }, []);

  async function submitCreate(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await createUser({ ...create, current_password: reauthentication });
      setCreate(emptyCreate);
      await refresh();
    } catch {
      setError(
        "Não foi possível criar o usuário. Confira os dados e sua senha.",
      );
    }
  }

  async function saveUser(
    user: AuthenticatedUser,
    changes: Partial<AuthenticatedUser>,
  ) {
    setError("");
    try {
      await updateUser(user.id, {
        ...(changes.name !== undefined ? { name: changes.name } : {}),
        ...(changes.role !== undefined ? { role: changes.role } : {}),
        ...(changes.active !== undefined ? { active: changes.active } : {}),
        current_password: reauthentication,
      });
      await refresh();
    } catch {
      setError(
        "Alteração não concluída. Confirme sua senha e tente novamente.",
      );
    }
  }

  async function recover(userId: string) {
    setError("");
    try {
      const result = await initiateRecovery(userId, reauthentication);
      setRecoveryCredential(result.credential);
    } catch {
      setError("Não foi possível iniciar a recuperação.");
    }
  }

  return (
    <section className="user-management">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Administração</p>
          <h3>Usuários</h3>
        </div>
        <label>
          Confirme sua senha
          <input
            aria-label="Senha do administrador"
            onChange={(event) => setReauthentication(event.target.value)}
            type="password"
            value={reauthentication}
          />
        </label>
      </div>
      {error ? (
        <p className="form-error" role="alert">
          {error}
        </p>
      ) : null}
      {recoveryCredential ? (
        <div className="recovery-result">
          <strong>Credencial de recuperação — exibida somente agora</strong>
          <code>{recoveryCredential}</code>
          <button onClick={() => setRecoveryCredential("")} type="button">
            Já copiei
          </button>
        </div>
      ) : null}
      <form
        className="create-user-form"
        onSubmit={(event) => void submitCreate(event)}
      >
        <input
          aria-label="Nome do novo usuário"
          onChange={(event) =>
            setCreate({ ...create, name: event.target.value })
          }
          placeholder="Nome"
          required
          value={create.name}
        />
        <input
          aria-label="E-mail do novo usuário"
          onChange={(event) =>
            setCreate({ ...create, email: event.target.value })
          }
          placeholder="E-mail"
          required
          type="email"
          value={create.email}
        />
        <select
          aria-label="Perfil do novo usuário"
          onChange={(event) =>
            setCreate({ ...create, role: event.target.value })
          }
          value={create.role}
        >
          <option value="cashier">Operador</option>
          <option value="manager">Gerente</option>
          <option value="administrator">Administrador</option>
        </select>
        <input
          aria-label="Senha temporária"
          minLength={12}
          onChange={(event) =>
            setCreate({ ...create, temporary_password: event.target.value })
          }
          placeholder="Senha temporária"
          required
          type="password"
          value={create.temporary_password}
        />
        <button type="submit">Adicionar usuário</button>
      </form>
      <div className="user-list">
        {users.map((user) => (
          <UserRow
            current={user.id === currentUserId}
            key={user.id}
            onRecover={() => void recover(user.id)}
            onSave={(changes) => void saveUser(user, changes)}
            user={user}
          />
        ))}
      </div>
    </section>
  );
}

function UserRow({
  user,
  current,
  onSave,
  onRecover,
}: {
  user: AuthenticatedUser;
  current: boolean;
  onSave: (changes: Partial<AuthenticatedUser>) => void;
  onRecover: () => void;
}) {
  const [name, setName] = useState(user.name);
  const [role, setRole] = useState(user.role);
  return (
    <article className="user-row">
      <input
        aria-label={`Nome de ${user.email}`}
        onChange={(event) => setName(event.target.value)}
        value={name}
      />
      <span>{user.email}</span>
      <select
        aria-label={`Perfil de ${user.email}`}
        onChange={(event) => setRole(event.target.value)}
        value={role}
      >
        <option value="cashier">Operador</option>
        <option value="manager">Gerente</option>
        <option value="administrator">Administrador</option>
      </select>
      <span className={user.active ? "status-active" : "status-inactive"}>
        {user.active ? "Ativo" : "Inativo"}
      </span>
      <div className="row-actions">
        <button onClick={() => onSave({ name, role })} type="button">
          Salvar
        </button>
        <button
          disabled={current}
          onClick={() => onSave({ active: !user.active })}
          type="button"
        >
          {user.active ? "Desativar" : "Reativar"}
        </button>
        <button disabled={!user.active} onClick={onRecover} type="button">
          Recuperar senha
        </button>
      </div>
    </article>
  );
}
