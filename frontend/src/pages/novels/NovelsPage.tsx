import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router";

import { apiFetch, errorMessage } from "../../shared/api";

type NovelStatus = "interview" | "ready" | "in_progress" | "published";

// Modelo `NovelSummary` del backend (008-brief-y-entrevista); `schema.d.ts` no lo tiene todavía
// (023, alcance) así que se declara aquí igual, sin inventar campos.
type NovelSummary = {
  id: number;
  title: string;
  recipient_name: string;
  status: NovelStatus;
  current_version: number | null;
  created_at: string;
};

type Load =
  | { status: "loading" }
  | { status: "ready"; novels: NovelSummary[] }
  | { status: "error" };

// Un estado por cada valor de `definitions.md` §3, sin caso por defecto (023-I1): un estado nuevo
// no cubierto aquí es un error de tipos, no una etiqueta genérica.
const STATUS_LABELS: Record<NovelStatus, string> = {
  interview: "En entrevista",
  ready: "Lista para escribir",
  in_progress: "Escribiéndose",
  published: "Publicada",
};

function useNovels(): [Load, () => void] {
  const [attempt, setAttempt] = useState(0);
  const [load, setLoad] = useState<Load>({ status: "loading" });
  useEffect(() => {
    let current = true;
    void apiFetch("/api/novels")
      .then((response) => {
        if (!response.ok) throw new Error("fallo al cargar /api/novels");
        return response.json() as Promise<NovelSummary[]>;
      })
      .then((novels) => {
        if (current) setLoad({ status: "ready", novels });
      })
      .catch(() => {
        if (current) setLoad({ status: "error" });
      });
    return () => {
      current = false;
    };
  }, [attempt]);
  const retry = () => {
    setLoad({ status: "loading" });
    setAttempt((n) => n + 1);
  };
  return [load, retry];
}

function LoadError({ onRetry }: { onRetry: () => void }) {
  return (
    <p role="alert" className="mb-6 rounded bg-accent px-3 py-2">
      No se pudo cargar la lista de novelas.{" "}
      <button type="button" onClick={onRetry} className="underline">
        Reintentar
      </button>
    </p>
  );
}

// El destino de una fila según su estado y su versión vigente (023-C09): con versión vigente
// (publicada, o `in_progress` tras un cambio del lector) va a la lectura; en entrevista o lista
// para escribir, a la entrevista; `in_progress` sin versión vigente (primera generación), al
// progreso.
function destinationOf(novel: NovelSummary): string {
  if (novel.current_version !== null) return `/novelas/${novel.id}/lectura`;
  if (novel.status === "in_progress") return `/novelas/${novel.id}/progreso`;
  return `/novelas/${novel.id}/entrevista`;
}

function NovelRow({ novel }: { novel: NovelSummary }) {
  const title = novel.title.trim() === "" ? "Sin título todavía" : novel.title;
  const date = new Date(novel.created_at).toLocaleDateString("es-ES");
  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-1 py-3">
      <Link
        to={destinationOf(novel)}
        className="font-reading text-lg font-semibold text-primary underline"
      >
        {title}
      </Link>
      <span>Para {novel.recipient_name}</span>
      <span className="rounded-full bg-accent px-2 py-0.5 text-sm text-secondary">
        {STATUS_LABELS[novel.status]}
      </span>
      {novel.current_version !== null && (
        <span className="text-sm text-secondary/70">v{novel.current_version}</span>
      )}
      <span className="text-sm text-secondary/70">{date}</span>
    </li>
  );
}

type CreateState = { submitting: boolean; error?: string };

// «Crear novela» (023-C07, 023-C08): crea una novela vacía y navega a su entrevista; un fallo se
// muestra y deja el botón disponible otra vez (023-I4).
function CreateNovelButton() {
  const navigate = useNavigate();
  const [state, setState] = useState<CreateState>({ submitting: false });

  async function handleClick() {
    setState({ submitting: true });
    const response = await apiFetch("/api/novels", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    if (response.status === 201) {
      const created = (await response.json()) as NovelSummary;
      await navigate(`/novelas/${created.id}/entrevista`);
      return;
    }
    setState({ submitting: false, error: await errorMessage(response) });
  }

  return (
    <div className="mb-8">
      <button
        type="button"
        disabled={state.submitting}
        onClick={() => void handleClick()}
        className="rounded bg-primary px-4 py-2 text-sm font-semibold text-secondary disabled:opacity-50"
      >
        Crear novela
      </button>
      {state.error && (
        <p role="alert" className="mt-3 rounded bg-accent px-3 py-2 text-sm">
          {state.error}
        </p>
      )}
    </div>
  );
}

// Lista prohibida de nivel `user` (023-C10 a 023-C15): forma normalizada de `005-guardarrailes`,
// declarada aquí igual que `NovelSummary` (023, alcance; `schema.d.ts` no la tiene todavía).
type TermType = "word" | "topic";
type BannedTermEntry = {
  id: number;
  term: string;
  type: TermType;
  keywords: string[];
};

type BannedList =
  | { status: "loading" }
  | { status: "ready"; entries: BannedTermEntry[] }
  | { status: "error" };

function useBannedTerms(): [
  BannedList,
  (entry: BannedTermEntry) => void,
  (id: number) => void,
] {
  const [list, setList] = useState<BannedList>({ status: "loading" });
  useEffect(() => {
    let current = true;
    void apiFetch("/api/banned-terms")
      .then((response) => {
        if (!response.ok) throw new Error("fallo al cargar /api/banned-terms");
        return response.json() as Promise<BannedTermEntry[]>;
      })
      .then((entries) => {
        if (current) setList({ status: "ready", entries });
      })
      .catch(() => {
        if (current) setList({ status: "error" });
      });
    return () => {
      current = false;
    };
  }, []);
  const add = (entry: BannedTermEntry) => {
    setList((current) =>
      current.status === "ready" ? { status: "ready", entries: [...current.entries, entry] } : current,
    );
  };
  const remove = (id: number) => {
    setList((current) =>
      current.status === "ready"
        ? { status: "ready", entries: current.entries.filter((e) => e.id !== id) }
        : current,
    );
  };
  return [list, add, remove];
}

function splitKeywords(input: string): string[] {
  return input
    .split(",")
    .map((keyword) => keyword.trim())
    .filter((keyword) => keyword !== "");
}

type BannedFormState = { term: string; type: TermType; keywords: string; submitting: boolean; error?: string };

function BannedTermRow({ entry, onDeleted }: { entry: BannedTermEntry; onDeleted: (id: number) => void }) {
  async function handleDelete() {
    const response = await apiFetch(`/api/banned-terms/${entry.id}`, { method: "DELETE" });
    if (response.status === 204) onDeleted(entry.id);
  }
  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2">
      <span className="font-medium text-secondary">{entry.term}</span>
      {entry.type === "topic" && entry.keywords.length > 0 && (
        <span className="text-sm text-secondary/70">({entry.keywords.join(", ")})</span>
      )}
      <button type="button" onClick={() => void handleDelete()} className="text-sm underline">
        Borrar {entry.term}
      </button>
    </li>
  );
}

function BannedTermsPanel() {
  const [list, add, remove] = useBannedTerms();
  const [form, setForm] = useState<BannedFormState>({ term: "", type: "word", keywords: "", submitting: false });

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setForm((f) => ({ ...f, submitting: true, error: undefined }));
    const keywords = form.type === "topic" ? splitKeywords(form.keywords) : [];
    const response = await apiFetch("/api/banned-terms", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ term: form.term, type: form.type, keywords }),
    });
    if (response.status === 201) {
      const created = (await response.json()) as BannedTermEntry;
      add(created);
      setForm({ term: "", type: "word", keywords: "", submitting: false });
      return;
    }
    const message = response.status === 409 ? "Ese término ya está en la lista." : await errorMessage(response);
    setForm((f) => ({ ...f, submitting: false, error: message }));
  }

  return (
    <section aria-label="Palabras y temas prohibidos" className="mt-10">
      <h3 className="mb-4 text-lg font-semibold text-secondary">Prohibidas</h3>
      {list.status === "loading" && <p role="status">Cargando la lista prohibida…</p>}
      {list.status === "error" && <p role="alert">No se pudo cargar la lista prohibida.</p>}
      {list.status === "ready" && (
        <ul aria-label="Prohibidas" className="mb-4 divide-y divide-secondary/10">
          {list.entries.map((entry) => (
            <BannedTermRow key={entry.id} entry={entry} onDeleted={remove} />
          ))}
        </ul>
      )}
      <form onSubmit={(event) => void handleSubmit(event)} className="flex flex-wrap items-end gap-3">
        <label className="flex flex-col text-sm">
          Término
          <input
            aria-label="Término"
            value={form.term}
            onChange={(event) => setForm((f) => ({ ...f, term: event.target.value }))}
            className="rounded border border-secondary/30 p-2"
          />
        </label>
        <label className="flex items-center gap-1 text-sm">
          <input
            type="radio"
            name="banned-type"
            checked={form.type === "word"}
            onChange={() => setForm((f) => ({ ...f, type: "word" }))}
          />
          Palabra
        </label>
        <label className="flex items-center gap-1 text-sm">
          <input
            type="radio"
            name="banned-type"
            aria-label="Tema"
            checked={form.type === "topic"}
            onChange={() => setForm((f) => ({ ...f, type: "topic" }))}
          />
          Tema
        </label>
        {form.type === "topic" && (
          <label className="flex flex-col text-sm">
            Palabras clave
            <input
              aria-label="Palabras clave"
              value={form.keywords}
              onChange={(event) => setForm((f) => ({ ...f, keywords: event.target.value }))}
              className="rounded border border-secondary/30 p-2"
            />
          </label>
        )}
        <button
          type="submit"
          disabled={form.submitting}
          className="rounded bg-primary px-4 py-2 text-sm font-semibold text-secondary disabled:opacity-50"
        >
          Añadir
        </button>
      </form>
      {form.error && (
        <p role="alert" className="mt-3 rounded bg-accent px-3 py-2 text-sm">
          {form.error}
        </p>
      )}
    </section>
  );
}

export function NovelsPage() {
  const [load, retry] = useNovels();
  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h2 className="mb-6 text-xl font-semibold text-secondary">Mis novelas</h2>
      <CreateNovelButton />
      {load.status === "loading" && <p role="status">Cargando tus novelas…</p>}
      {load.status === "error" && <LoadError onRetry={retry} />}
      {load.status === "ready" && load.novels.length === 0 && (
        <p>Aún no tienes ninguna novela todavía.</p>
      )}
      {load.status === "ready" && load.novels.length > 0 && (
        <ul aria-label="Novelas" className="divide-y divide-secondary/10">
          {load.novels.map((novel) => (
            <NovelRow key={novel.id} novel={novel} />
          ))}
        </ul>
      )}
      <BannedTermsPanel />
    </main>
  );
}
