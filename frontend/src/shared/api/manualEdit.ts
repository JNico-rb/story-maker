import { apiFetch } from "./apiFetch";

export type DiagnosticType =
  | "forma_no_canonica"
  | "personaje_desconocido"
  | "hecho"
  | "prohibida"
  | "linter"
  | "cronologia";

// Contrato de specs/backend/019-edicion-manual.md (código del carril F, manda sobre lo que
// asumiera este cliente): la API real aún no está en V2, así que 028 la simula en el límite del
// cliente (frontend/AGENTS.md), igual que 027 hizo con 014. `blocking` viene ya resuelta por la
// API (028-I4): la pantalla nunca decide por su cuenta si algo bloqueará el guardado.
export type Diagnostic = {
  type: DiagnosticType;
  message: string;
  position?: { start: number; end: number };
  blocking: boolean;
};

export async function lintChapter(novelId: string, chapter: number, text: string): Promise<Response> {
  return apiFetch(`/api/novels/${novelId}/chapters/${chapter}/lint`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  });
}

export async function saveChapter(
  novelId: string,
  chapter: number,
  text: string,
  baseVersion: number,
): Promise<Response> {
  return apiFetch(`/api/novels/${novelId}/chapters/${chapter}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, base_version: baseVersion }),
  });
}
