const BASE = "/api/v1";

function getCsrfToken(): string {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : "";
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  options: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "X-CSRFToken": getCsrfToken(),
    ...((options.headers as Record<string, string>) || {}),
  };

  const resp = await fetch(`${BASE}${path}`, {
    method,
    credentials: "include",
    headers,
    body: body !== undefined ? JSON.stringify(body) : undefined,
    ...options,
  });

  if (resp.status === 204 || resp.status === 304) {
    return undefined as T;
  }

  const data = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    const error = new ApiError(resp.status, data);
    throw error;
  }

  return data as T;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public data: Record<string, unknown>
  ) {
    super(String(data?.title || data?.detail || "Erro desconhecido"));
    this.name = "ApiError";
  }
}

export const api = {
  get: <T>(path: string) => request<T>("GET", path),
  post: <T>(path: string, body?: unknown) => request<T>("POST", path, body),
  patch: <T>(path: string, body?: unknown) => request<T>("PATCH", path, body),
  delete: <T>(path: string) => request<T>("DELETE", path),

  postForm: async <T>(path: string, form: FormData): Promise<T> => {
    const resp = await fetch(`${BASE}${path}`, {
      method: "POST",
      credentials: "include",
      headers: { "X-CSRFToken": getCsrfToken() },
      body: form,
    });
    if (!resp.ok) {
      const data = await resp.json().catch(() => ({}));
      throw new ApiError(resp.status, data);
    }
    return resp.json() as Promise<T>;
  },
};
