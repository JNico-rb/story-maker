// Sesión guardada: el token que devolvió un acceso válido, hasta que se borra.
let token: string | null = null;

export function readSession(): string | null {
  return token;
}

export function saveSession(value: string): void {
  token = value;
}

export function clearSession(): void {
  token = null;
}
