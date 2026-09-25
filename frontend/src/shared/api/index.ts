// Cliente HTTP tipado con los tipos de schema.d.ts (`pnpm gen:api`).
export { apiFetch } from "./apiFetch";
export { invalidFields } from "./invalidFields";
export { errorMessage } from "./errorMessage";
export { confirmChange, requestChange } from "./changeRequests";
export type { ChangeConfirmed, ChangeRequestCreated, Proposal, Selection } from "./changeRequests";
export { lintChapter, saveChapter } from "./manualEdit";
export type { Diagnostic, DiagnosticType } from "./manualEdit";
