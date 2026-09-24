// Sesión guardada: el token que devolvió un acceso válido, hasta que se borra.
let token: string | null = null;
const listeners = new Set<() => void>();

export function readSession(): string | null {
  return token;
}

export function saveSession(value: string): void {
  token = value;
  listeners.forEach((listener) => listener());
}

export function clearSession(): void {
  token = null;
  listeners.forEach((listener) => listener());
}

export function subscribeSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
