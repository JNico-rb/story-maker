import { clearSession, readSession } from "../lib";

// Petición a una ruta protegida de /api. Sin sesión guardada no sale nada (spec 022, I4); el
// token viaja solo en la cabecera (spec 002) y un 401 es una sesión rechazada: se borra.
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const token = readSession();
  if (!token) throw new Error("sin sesión guardada");
  const headers = new Headers(init.headers);
  headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(path, { ...init, headers });
  if (response.status === 401) clearSession();
  return response;
}
