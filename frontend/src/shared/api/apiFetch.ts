import { clearSession, readSession } from "../lib";

// Petición a una ruta protegida de /api. El token viaja solo en la cabecera (spec 002);
// un 401 es una sesión rechazada por el servidor y se borra.
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${readSession() ?? ""}`);
  const response = await fetch(path, { ...init, headers });
  if (response.status === 401) clearSession();
  return response;
}
