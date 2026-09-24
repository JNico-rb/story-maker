import { apiFetch } from "./apiFetch";

// Contrato real de specs/backend/014-cambios-del-lector.md (código del carril A, manda sobre lo
// que asumiera este cliente): la API real aún no está en V2, así que 027 la simula en el límite
// del cliente (frontend/AGENTS.md). `selection` es siempre un fragmento — la lectura no expone
// hechos ni sus ids (027, fuera de alcance) — y no admite más campos que estos.
export type Selection = { type: "fragment"; version: number; chapter: number; quote: string };

export type Proposal =
  | { fact: string; old_value: string; new_value: string }
  | { new_fact: string };

export type ChangeRequestCreated = {
  id: string;
  proposal: Proposal;
  affected_chapters: number[];
  code: string;
  expires_at: string;
};

export type ChangeConfirmed = { run_id: string };

export async function requestChange(novelId: string, selection: Selection, request: string): Promise<Response> {
  return apiFetch(`/api/novels/${novelId}/change-requests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ selection, request }),
  });
}

export async function confirmChange(requestId: string, code: string): Promise<Response> {
  return apiFetch(`/api/change-requests/${requestId}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ code }),
  });
}
