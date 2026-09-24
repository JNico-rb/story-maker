// Sesión guardada: el token que devolvió un acceso válido, hasta que se borra. Vive en
// localStorage para sobrevivir a una recarga (spec 022, I3); nunca en una cookie.
const KEY = "story-maker.session";
const listeners = new Set<() => void>();

export function readSession(): string | null {
  return localStorage.getItem(KEY);
}

export function saveSession(value: string): void {
  localStorage.setItem(KEY, value);
  listeners.forEach((listener) => listener());
}

export function clearSession(): void {
  localStorage.removeItem(KEY);
  listeners.forEach((listener) => listener());
}

export function subscribeSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
