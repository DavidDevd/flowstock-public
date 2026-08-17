import { useEffect, useState } from "react";

import { LoginPage } from "../features/identity/LoginPage";
import { WorkspacePage } from "../features/identity/WorkspacePage";
import { getSession, logout, type AuthenticatedUser } from "../lib/auth";
import { App } from "./App";

export function AppRouter() {
  const [user, setUser] = useState<AuthenticatedUser | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getSession()
      .then(setUser)
      .catch(() => setUser(null))
      .finally(() => setLoading(false));
  }, []);

  async function leave() {
    await logout();
    setUser(null);
  }

  return (
    <App>
      {loading ? (
        <p className="loading-state">Carregando ambiente seguro…</p>
      ) : null}
      {!loading && !user ? <LoginPage onAuthenticated={setUser} /> : null}
      {!loading && user ? (
        <WorkspacePage onLogout={() => void leave()} user={user} />
      ) : null}
    </App>
  );
}
