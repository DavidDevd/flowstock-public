import { useQuery } from "@tanstack/react-query";

import { fetchReadiness } from "../../lib/api";

export function PlatformStatusPage() {
  const readiness = useQuery({
    queryKey: ["platform-readiness"],
    queryFn: ({ signal }) => fetchReadiness(signal),
  });

  const status = readiness.isPending
    ? "Verificando"
    : readiness.isError
      ? "Indisponível"
      : "Operacional";

  return (
    <section className="status-card" aria-labelledby="platform-title">
      <div className="status-card__heading">
        <div>
          <p className="eyebrow">Plataforma</p>
          <h2 id="platform-title">Fundação pronta para evoluir</h2>
        </div>
        <span
          className={`status-pill status-pill--${readiness.isError ? "error" : "ok"}`}
          aria-live="polite"
        >
          {status}
        </span>
      </div>

      <p>
        O shell web, a API e a infraestrutura de qualidade foram inicializados.
        Funcionalidades operacionais começam apenas nas sprints previstas no
        backlog aprovado.
      </p>

      <dl className="foundation-grid">
        <div>
          <dt>Interface</dt>
          <dd>React + TypeScript</dd>
        </div>
        <div>
          <dt>API</dt>
          <dd>FastAPI modular</dd>
        </div>
        <div>
          <dt>Persistência</dt>
          <dd>PostgreSQL</dd>
        </div>
        <div>
          <dt>Ambiente</dt>
          <dd>Development</dd>
        </div>
      </dl>

      {readiness.isError ? (
        <p className="status-message status-message--error">
          A API ou o banco ainda não respondeu. Use o identificador de
          correlação dos logs para diagnóstico.
        </p>
      ) : null}
    </section>
  );
}
