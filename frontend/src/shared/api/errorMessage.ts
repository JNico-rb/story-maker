// `detail` de un error de la API (api/errors.py) puede ser un string, una lista de
// {loc,msg,type} o un objeto (p. ej. con `defects`); esto entrega siempre un texto legible sin
// depender de más forma que esa (014-cambios-del-lector, alcance del frontend).
export async function errorMessage(response: Response): Promise<string> {
  const body = (await response.json().catch(() => null)) as { detail?: unknown } | null;
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((issue) => (issue && typeof issue === "object" && "msg" in issue ? String(issue.msg) : JSON.stringify(issue)))
      .join("; ");
  }
  if (detail && typeof detail === "object") return JSON.stringify(detail);
  return "No se pudo completar la operación.";
}
