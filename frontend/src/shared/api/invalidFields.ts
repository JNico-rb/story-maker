type ValidationIssue = { loc?: unknown };

// Un 422 de FastAPI lista en `detail` cada campo sin forma válida; `loc` acaba en su nombre.
export async function invalidFields(response: Response): Promise<Set<string>> {
  const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  const issues = Array.isArray(body?.detail) ? (body.detail as ValidationIssue[]) : [];
  return new Set(
    issues.flatMap((issue) => (Array.isArray(issue.loc) ? [String(issue.loc.at(-1))] : [])),
  );
}
