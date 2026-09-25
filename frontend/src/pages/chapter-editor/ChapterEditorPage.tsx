import { useEffect, useRef, useState } from "react";
import { useNavigate, useParams } from "react-router";

import { apiFetch, errorMessage, lintChapter, saveChapter, type Diagnostic } from "../../shared/api";
import type { components } from "../../shared/api/schema";

type VersionDetail = components["schemas"]["VersionDetailResponse"];
type VersionsList = components["schemas"]["VersionsListResponse"];

// Pausa fija entre la última pulsación y la petición de lint (028-C04); los docs no fijan un
// valor, así que queda como constante simple de la pantalla (autorrevisión de la spec).
const LINT_DEBOUNCE_MS = 500;

async function fetchChapterText(novelId: string, version: number, chapter: number): Promise<string> {
  const response = await apiFetch(`/api/novels/${novelId}/versions/${version}`);
  if (!response.ok) throw new Error("fallo al cargar el capítulo");
  const data = (await response.json()) as VersionDetail;
  const found = data.view.chapters.find((c) => c.number === chapter);
  if (!found) throw new Error("capítulo no encontrado");
  return found.text;
}

async function fetchCurrentVersion(novelId: string): Promise<number> {
  const response = await apiFetch(`/api/novels/${novelId}/versions`);
  if (!response.ok) throw new Error("fallo al cargar las versiones");
  const data = (await response.json()) as VersionsList;
  const latest = data.versions.at(-1)?.number;
  if (latest === undefined) throw new Error("sin versión publicada");
  return latest;
}

function Loading({ children }: { children: string }) {
  return (
    <p role="status" className="mb-6 animate-pulse text-secondary/70">
      {children}
    </p>
  );
}

function LoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <p
      role="alert"
      className="mb-6 flex flex-wrap items-center gap-3 break-words rounded-lg border border-primary/40 bg-accent px-4 py-3"
    >
      <span>{message}</span>
      <button
        type="button"
        onClick={onRetry}
        className="rounded bg-primary px-3 py-1 text-sm font-semibold text-secondary"
      >
        Reintentar
      </button>
    </p>
  );
}

function DiagnosticItem({ diagnostic }: { diagnostic: Diagnostic }) {
  return (
    <li className="rounded border border-secondary/20 bg-white/70 px-3 py-2 text-sm break-words">
      <span>{diagnostic.message}</span>
      <span className={diagnostic.blocking ? "ml-2 font-semibold text-primary" : "ml-2 text-secondary/60"}>
        {diagnostic.blocking ? "bloqueará el guardado" : "aviso"}
      </span>
    </li>
  );
}

type SaveState =
  | { kind: "idle" }
  | { kind: "saving" }
  | { kind: "rejected"; diagnostics: Diagnostic[] }
  | { kind: "stale" }
  | { kind: "error"; message: string };

function ChapterEditor({
  novelId,
  chapter,
  version,
  initialText,
  onSaved,
  onStaleReload,
}: {
  novelId: string;
  chapter: number;
  version: number;
  initialText: string;
  onSaved: () => void;
  onStaleReload: () => void;
}) {
  const [text, setText] = useState(initialText);
  const [diagnostics, setDiagnostics] = useState<Diagnostic[]>([]);
  const [lintFailed, setLintFailed] = useState(false);
  const [save, setSave] = useState<SaveState>({ kind: "idle" });
  const sentSeq = useRef(0);

  // 028-C04, 028-C08, 028-I2: solo un lint por pausa de escritura; `sentSeq` marca cada envío para
  // que una respuesta tardía de un envío anterior nunca sustituya a la de uno más reciente.
  useEffect(() => {
    const timer = setTimeout(() => {
      const mySeq = ++sentSeq.current;
      void lintChapter(novelId, chapter, text)
        .then(async (response) => {
          if (mySeq !== sentSeq.current) return;
          if (!response.ok) {
            setLintFailed(true);
            return;
          }
          const body = (await response.json()) as { diagnostics: Diagnostic[] };
          setLintFailed(false);
          setDiagnostics(body.diagnostics);
        })
        .catch(() => {
          // 028-C09: un fallo del lint conserva los diagnósticos que ya había.
          if (mySeq === sentSeq.current) setLintFailed(true);
        });
    }, LINT_DEBOUNCE_MS);
    return () => clearTimeout(timer);
  }, [text, novelId, chapter]);

  async function handleSave() {
    setSave({ kind: "saving" });
    const response = await saveChapter(novelId, chapter, text, version);
    if (response.status === 202) {
      await response.json();
      onSaved();
      return;
    }
    if (response.status === 422) {
      const body = (await response.json()) as { detail: { diagnostics: Diagnostic[] } };
      setSave({ kind: "rejected", diagnostics: body.detail.diagnostics });
      return;
    }
    if (response.status === 409) {
      setSave({ kind: "stale" });
      return;
    }
    setSave({ kind: "error", message: await errorMessage(response) });
  }

  const positioned = diagnostics.filter((d) => d.position !== undefined);
  const unpositioned = diagnostics.filter((d) => d.position === undefined);
  const rejected = save.kind === "rejected" ? save.diagnostics : [];

  return (
    <section aria-label="Editor del capítulo" className="mx-auto max-w-prose break-words">
      <label htmlFor="chapter-editor-text" className="mb-2 block text-sm font-medium text-secondary">
        Texto del capítulo
      </label>
      <textarea
        id="chapter-editor-text"
        value={text}
        onChange={(event) => setText(event.target.value)}
        rows={20}
        className="w-full rounded border border-secondary/30 p-3 font-reading"
      />

      {lintFailed && (
        <p role="alert" className="mt-2 text-sm">
          No se pudo comprobar el texto.
        </p>
      )}

      {positioned.length > 0 && (
        <ul aria-label="Avisos en el texto" className="mt-3 space-y-2">
          {positioned.map((diagnostic, index) => (
            <li key={index} className="rounded border border-secondary/20 bg-white/70 px-3 py-2 text-sm break-words">
              <mark className={diagnostic.blocking ? "bg-primary/30" : "bg-accent"}>
                {text.slice(diagnostic.position!.start, diagnostic.position!.end)}
              </mark>
              <span className="ml-2">{diagnostic.message}</span>
              <span className={diagnostic.blocking ? "ml-2 font-semibold text-primary" : "ml-2 text-secondary/60"}>
                {diagnostic.blocking ? "bloqueará el guardado" : "aviso"}
              </span>
            </li>
          ))}
        </ul>
      )}

      {unpositioned.length > 0 && (
        <ul aria-label="Otros avisos" className="mt-3 space-y-2">
          {unpositioned.map((diagnostic, index) => (
            <DiagnosticItem key={index} diagnostic={diagnostic} />
          ))}
        </ul>
      )}

      {save.kind === "rejected" && (
        <>
          <p role="alert" className="mt-3 text-sm">
            No se pudo guardar: hay avisos que lo bloquean.
          </p>
          <ul aria-label="Diagnósticos del guardado" className="mt-2 space-y-2">
            {rejected.map((diagnostic, index) => (
              <DiagnosticItem key={index} diagnostic={diagnostic} />
            ))}
          </ul>
        </>
      )}

      {save.kind === "stale" && (
        <p role="alert" className="mt-3 flex flex-wrap items-center gap-3 text-sm">
          <span>Hay una versión más nueva publicada.</span>
          <button
            type="button"
            onClick={onStaleReload}
            className="rounded bg-primary px-3 py-1 text-sm font-semibold text-secondary"
          >
            Recargar el capítulo vigente
          </button>
        </p>
      )}

      {save.kind === "error" && (
        <p role="alert" className="mt-3 text-sm">
          {save.message}
        </p>
      )}

      <button
        type="button"
        disabled={save.kind === "saving"}
        onClick={() => void handleSave()}
        className="mt-4 rounded bg-primary px-4 py-2 text-sm font-semibold text-secondary disabled:opacity-50"
      >
        Guardar
      </button>
    </section>
  );
}

type ChapterLoad = { status: "loading" } | { status: "error" } | { status: "ready"; text: string; version: number };

export function ChapterEditorPage() {
  const { novelId = "", version = "", chapterNumber = "" } = useParams();
  const navigate = useNavigate();
  const chapter = Number(chapterNumber);
  const [state, setState] = useState<ChapterLoad>({ status: "loading" });
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    let current = true;
    void fetchChapterText(novelId, Number(version), chapter)
      .then((text) => {
        if (current) setState({ status: "ready", text, version: Number(version) });
      })
      .catch(() => {
        if (current) setState({ status: "error" });
      });
    return () => {
      current = false;
    };
  }, [novelId, version, chapter, attempt]);

  function retry() {
    setState({ status: "loading" });
    setAttempt((n) => n + 1);
  }

  async function handleStaleReload() {
    try {
      const latest = await fetchCurrentVersion(novelId);
      const text = await fetchChapterText(novelId, latest, chapter);
      setState({ status: "ready", text, version: latest });
    } catch {
      // Recargar es un mejor esfuerzo: si falla, el aviso de base obsoleta sigue visible.
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      {state.status === "loading" && <Loading>Cargando el capítulo…</Loading>}
      {state.status === "error" && <LoadError message="No se pudo cargar el capítulo." onRetry={retry} />}
      {state.status === "ready" && (
        <ChapterEditor
          key={state.version}
          novelId={novelId}
          chapter={chapter}
          version={state.version}
          initialText={state.text}
          onSaved={() => navigate(`/novelas/${novelId}/progreso`)}
          onStaleReload={() => void handleStaleReload()}
        />
      )}
    </main>
  );
}
