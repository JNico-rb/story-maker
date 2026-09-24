import { readSession } from "../lib";

// Petición a una ruta protegida de /api. El token viaja solo en la cabecera (spec 002).
export function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${readSession() ?? ""}`);
  return fetch(path, { ...init, headers });
}
