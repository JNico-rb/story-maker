import { useEffect, useState } from "react";
import { Link } from "react-router";

import { apiFetch } from "../../shared/api";

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

function NovelRow({ novel }: { novel: NovelSummary }) {
  const title = novel.title.trim() === "" ? "Sin título todavía" : novel.title;
  const date = new Date(novel.created_at).toLocaleDateString("es-ES");
  return (
    <li className="flex flex-wrap items-center gap-x-4 gap-y-1 py-3">
      {novel.current_version !== null ? (
        <Link
          to={`/novelas/${novel.id}/lectura`}
          className="font-reading text-lg font-semibold text-primary underline"
        >
          {title}
        </Link>
      ) : (
        <span className="font-reading text-lg font-semibold text-secondary">{title}</span>
      )}
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

export function NovelsPage() {
  const [load, retry] = useNovels();
  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h2 className="mb-6 text-xl font-semibold text-secondary">Mis novelas</h2>
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
    </main>
  );
}
