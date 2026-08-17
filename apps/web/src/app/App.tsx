import type { PropsWithChildren } from "react";

export function App({ children }: PropsWithChildren) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Gestão inteligente de depósitos</p>
          <h1>FlowStock</h1>
        </div>
        <span className="release-badge">MVP</span>
      </header>
      <main className="app-content">{children}</main>
      <footer className="app-footer">
        FlowStock · Operação simples, segura e rastreável
      </footer>
    </div>
  );
}
