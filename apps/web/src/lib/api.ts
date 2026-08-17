export interface HealthResponse {
  status: "ok" | "not_ready";
  checks: Record<string, string>;
}

export async function fetchReadiness(
  signal?: AbortSignal,
): Promise<HealthResponse> {
  const response = await fetch("/api/v1/health/ready", {
    credentials: "same-origin",
    headers: {
      Accept: "application/json",
    },
    signal: signal ?? null,
  });

  if (!response.ok) {
    throw new Error("FlowStock platform is not ready.");
  }

  return (await response.json()) as HealthResponse;
}
