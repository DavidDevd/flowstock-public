export interface AuthenticatedUser {
  id: string;
  email: string;
  name: string;
  role: string;
  permissions: string[];
  must_change_password: boolean;
  active: boolean;
}

interface LoginResponse {
  user: AuthenticatedUser;
  csrf_token: string;
}

let csrfToken: string | null = null;

export async function apiRequest<T>(
  path: string,
  init?: RequestInit,
): Promise<T> {
  const headers = new Headers(init?.headers);
  headers.set("Accept", "application/json");
  if (init?.body) headers.set("Content-Type", "application/json");
  if (csrfToken && init?.method && init.method !== "GET") {
    headers.set("X-CSRF-Token", csrfToken);
  }
  const response = await fetch(`/api/v1${path}`, {
    ...init,
    credentials: "same-origin",
    headers,
  });
  if (!response.ok) {
    throw new Error(
      response.status === 401
        ? "Credenciais inválidas."
        : "Não foi possível concluir.",
    );
  }
  return response.status === 204
    ? (undefined as T)
    : ((await response.json()) as T);
}

export async function login(email: string, password: string) {
  const result = await apiRequest<LoginResponse>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ email, password }),
  });
  csrfToken = result.csrf_token;
  return result.user;
}

export function getSession() {
  return apiRequest<LoginResponse>("/auth/session").then((result) => {
    csrfToken = result.csrf_token;
    return result.user;
  });
}

export async function logout() {
  await apiRequest<void>("/auth/logout", { method: "POST" });
  csrfToken = null;
}

export function changePassword(currentPassword: string, newPassword: string) {
  return apiRequest<void>("/auth/password", {
    method: "POST",
    body: JSON.stringify({
      current_password: currentPassword,
      new_password: newPassword,
    }),
  });
}

export function listUsers() {
  return apiRequest<AuthenticatedUser[]>("/users");
}

export interface CreateUserInput {
  email: string;
  name: string;
  role: string;
  temporary_password: string;
  current_password: string;
}

export function createUser(input: CreateUserInput) {
  return apiRequest<AuthenticatedUser>("/users", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

export function updateUser(
  userId: string,
  input: {
    name?: string;
    role?: string;
    active?: boolean;
    current_password: string;
  },
) {
  return apiRequest<AuthenticatedUser>(`/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
  });
}

export async function initiateRecovery(
  userId: string,
  currentPassword: string,
) {
  return apiRequest<{ credential: string; expires_in_seconds: number }>(
    `/users/${userId}/recovery`,
    {
      method: "POST",
      body: JSON.stringify({ current_password: currentPassword }),
    },
  );
}

export function completeRecovery(
  email: string,
  credential: string,
  newPassword: string,
) {
  return apiRequest<void>("/auth/recovery/complete", {
    method: "POST",
    body: JSON.stringify({
      email,
      credential,
      new_password: newPassword,
    }),
  });
}
