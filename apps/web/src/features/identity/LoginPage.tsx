import { useState, type FormEvent } from "react";

import {
  completeRecovery,
  login,
  type AuthenticatedUser,
} from "../../lib/auth";

export function LoginPage({
  onAuthenticated,
}: {
  onAuthenticated: (user: AuthenticatedUser) => void;
}) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [recovering, setRecovering] = useState(false);
  const [recoveryCredential, setRecoveryCredential] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [recoveryComplete, setRecoveryComplete] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      onAuthenticated(await login(email, password));
    } catch (reason) {
      setError(
        reason instanceof Error ? reason.message : "Não foi possível entrar.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  async function recover(event: FormEvent) {
    event.preventDefault();
    setError("");
    try {
      await completeRecovery(email, recoveryCredential, newPassword);
      setRecoveryComplete(true);
      setRecovering(false);
    } catch {
      setError("Credencial de recuperação inválida ou expirada.");
    }
  }

  return (
    <section className="login-layout">
      <div className="login-intro">
        <p className="eyebrow">Operação de depósitos</p>
        <h2>Controle o negócio sem depender de planilhas.</h2>
        <p>Entre para acessar a operação segura do FlowStock.</p>
      </div>
      <form
        className="login-card"
        onSubmit={(event) => void (recovering ? recover(event) : submit(event))}
      >
        <h2>Entrar</h2>
        <label>
          E-mail
          <input
            autoComplete="username"
            onChange={(event) => setEmail(event.target.value)}
            required
            type="email"
            value={email}
          />
        </label>
        {recovering ? (
          <>
            <label>
              Credencial de recuperação
              <input
                onChange={(event) => setRecoveryCredential(event.target.value)}
                required
                value={recoveryCredential}
              />
            </label>
            <label>
              Nova senha
              <input
                minLength={12}
                onChange={(event) => setNewPassword(event.target.value)}
                required
                type="password"
                value={newPassword}
              />
            </label>
          </>
        ) : (
          <label>
            Senha
            <input
              autoComplete="current-password"
              maxLength={128}
              onChange={(event) => setPassword(event.target.value)}
              required
              type="password"
              value={password}
            />
          </label>
        )}
        {recoveryComplete ? (
          <p className="success-message">
            Senha alterada. Entre com a nova senha.
          </p>
        ) : null}
        {error ? (
          <p className="form-error" role="alert">
            {error}
          </p>
        ) : null}
        <button disabled={submitting} type="submit">
          {recovering
            ? "Definir nova senha"
            : submitting
              ? "Entrando…"
              : "Entrar"}
        </button>
        <button
          className="link-button"
          onClick={() => setRecovering(!recovering)}
          type="button"
        >
          {recovering ? "Voltar ao login" : "Usar credencial de recuperação"}
        </button>
      </form>
    </section>
  );
}
