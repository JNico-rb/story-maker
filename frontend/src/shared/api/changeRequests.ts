import { apiFetch } from "./apiFetch";

// Contrato de specs/backend/014-cambios-del-lector.md y architecture.md §15.7: la API real se
// implementa en otro carril y aún no está en V2, así que 027 la simula en el límite del cliente
// (frontend/AGENTS.md). La forma exacta de `selection` es de 027, no de 014 (fuera de su alcance).
export type Selection =
  | { kind: "fragment"; chapter: number; quote: string }
  | { kind: "fact"; fact_id: number; label: string; value: string };

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
