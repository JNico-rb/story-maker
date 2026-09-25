import { useEffect, useState } from "react";
import { useParams } from "react-router";

import { apiFetch } from "../../shared/api";
import type { components } from "../../shared/api/schema";
import type { Selection } from "../../shared/api";
import { ChangeRequestPanel } from "../reader-change";

type VersionsList = components["schemas"]["VersionsListResponse"];
type VersionDetail = components["schemas"]["VersionDetailResponse"];
type Load<T> = { status: "loading" } | { status: "ready"; data: T } | { status: "error" };

// Cada carga vive en un componente con `key`: cambiar de versión lo desmonta y la respuesta
// tardía de la anterior se descarta, así nunca se mezclan dos versiones (026-I1). Un fallo se
// muestra siempre, nunca se descarta en silencio ni deja contenido de una carga anterior (026-I4).
function useJson<T>(path: string): [Load<T>, () => void] {
  const [attempt, setAttempt] = useState(0);
  const [load, setLoad] = useState<Load<T>>({ status: "loading" });
  useEffect(() => {
    let current = true;
    void apiFetch(path)
      .then((response) => {
        if (!response.ok) throw new Error(`fallo al cargar ${path}`);
        return response.json() as Promise<T>;
      })
      .then((data) => {
        if (current) setLoad({ status: "ready", data });
      })
      .catch(() => {
        if (current) setLoad({ status: "error" });
      });
    return () => {
      current = false;
    };
  }, [path, attempt]);
  const retry = () => {
    setLoad({ status: "loading" });
    setAttempt((n) => n + 1);
  };
  return [load, retry];
}

// Aviso de carga accesible (026-C15): `role="status"` para lectores de pantalla, `animate-pulse`
// como indicador visual discreto. Desaparece en cuanto `load` deja de ser "loading".
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

function Cover({ view }: { view: VersionDetail["view"] }) {
  return (
    <section
      aria-label="Portada"
      className="mx-auto mb-12 max-w-2xl break-words rounded-lg border border-secondary/10 bg-white/60 px-4 py-10 text-center shadow-sm sm:px-10"
    >
      <h2 className="font-reading text-3xl font-semibold text-secondary sm:text-4xl">{view.title}</h2>
      <p className="mt-3 text-sm uppercase tracking-[0.2em] text-secondary/70">Para {view.recipient}</p>
      <hr className="mx-auto my-6 w-16 border-t-2 border-primary" />
      <p className="font-reading text-lg italic text-secondary">{view.dedication}</p>
    </section>
  );
}

function Index({
  chapters,
  changedChapters,
  version,
}: {
  chapters: VersionDetail["view"]["chapters"];
  changedChapters: number[];
  version: number;
}) {
  return (
    <nav aria-label="Índice" className="mx-auto mb-10 max-w-prose">
      <ol className="space-y-1">
        {chapters.map((chapter) => (
          <li key={chapter.number}>
            <a
              href={`#capitulo-${chapter.number}`}
              className="flex flex-wrap items-center justify-between gap-2 rounded px-2 py-1.5 break-words hover:bg-accent/50"
            >
              <span>
                Capítulo {chapter.number} · {chapter.title}
              </span>
              {changedChapters.includes(chapter.number) && (
                <span className="rounded-full bg-primary/20 px-2 py-0.5 text-xs font-semibold text-primary">
                  cambiado en v{version}
                </span>
              )}
            </a>
          </li>
        ))}
      </ol>
    </nav>
  );
}

function News({ changedChapters }: { changedChapters: number[] }) {
  if (changedChapters.length === 0) return null;
  return (
    <section
      aria-label="Novedades"
      className="mx-auto mb-10 max-w-prose rounded-lg border border-primary/30 bg-primary/10 px-4 py-4 sm:px-5"
    >
      <h3 className="font-reading text-lg font-semibold text-secondary">Novedades</h3>
      <ul className="mt-2 space-y-1">
        {changedChapters.map((number) => (
          <li key={number}>
            <a href={`#capitulo-${number}`} className="text-primary underline">
              Capítulo {number}
            </a>
          </li>
        ))}
      </ul>
    </section>
  );
}

// El texto llega en una sola cadena; una línea en blanco separa párrafos (026-C16, pulido).
function paragraphsOf(text: string): string[] {
  const parts = text.split(/\n\s*\n/).map((part) => part.trim()).filter((part) => part !== "");
  return parts.length > 0 ? parts : [text];
}

function Chapter({
  chapter,
  onSelectFragment,
}: {
  chapter: VersionDetail["view"]["chapters"][number];
  onSelectFragment: (chapter: number, quote: string) => void;
}) {
  function handleMouseUp() {
    const quote = window.getSelection()?.toString().trim() ?? "";
    if (quote) onSelectFragment(chapter.number, quote);
  }
  return (
    <section
      id={`capitulo-${chapter.number}`}
      aria-label={`Capítulo ${chapter.number}`}
      className="mx-auto mb-12 max-w-prose break-words"
      onMouseUp={handleMouseUp}
    >
      <h3 className="font-reading text-2xl font-semibold text-secondary">{chapter.title}</h3>
      <div className="mt-4 space-y-4 font-reading text-lg leading-relaxed">
        {paragraphsOf(chapter.text).map((paragraph, index) => (
          <p key={index}>{paragraph}</p>
        ))}
      </div>
    </section>
  );
}

// 027: un fragmento seleccionado en un capítulo habilita «pedir un cambio», que abre el panel
// de 027 con esa selección (versión vigente, capítulo, cita literal).
function ChangeRequestEntryPoint({
  novelId,
  version,
  fragment,
  onClear,
}: {
  novelId: string;
  version: number;
  fragment: { chapter: number; quote: string } | null;
  onClear: () => void;
}) {
  const [selection, setSelection] = useState<Selection | null>(null);
  const [runInProgress, setRunInProgress] = useState<string | null>(null);

  if (runInProgress) {
    return (
      <p className="mx-auto mb-10 max-w-prose rounded-lg border border-secondary/10 bg-accent/40 px-4 py-3 text-sm">
        El cambio está en marcha (ejecución {runInProgress}).
      </p>
    );
  }

  if (selection) {
    return (
      <ChangeRequestPanel
        novelId={novelId}
        selection={selection}
        onDiscard={() => {
          setSelection(null);
          onClear();
        }}
        onConfirmed={(runId) => {
          setSelection(null);
          onClear();
          setRunInProgress(runId);
        }}
      />
    );
  }

  if (!fragment) return null;

  return (
    <div className="mx-auto mb-10 max-w-prose">
      <button
        type="button"
        onClick={() => setSelection({ type: "fragment", version, chapter: fragment.chapter, quote: fragment.quote })}
        className="rounded bg-primary px-4 py-2 text-sm font-semibold text-secondary"
      >
        Pedir un cambio
      </button>
    </div>
  );
}

// Kind del detalle (personaje/lugar): agrupa la ficha para que se lea de un vistazo.
const KIND_LABELS: Record<string, string> = { personaje: "Personajes", lugar: "Lugares" };

function Ficha({ entities }: { entities: VersionDetail["view"]["ficha"] }) {
  const groups = new Map<string, typeof entities>();
  for (const entity of entities) {
    const group = groups.get(entity.kind) ?? [];
    group.push(entity);
    groups.set(entity.kind, group);
  }
  return (
    <section aria-label="Ficha" className="mx-auto mb-10 max-w-prose break-words">
      <h3 className="font-reading text-xl font-semibold text-secondary">Ficha</h3>
      {[...groups.entries()].map(([kind, group]) => (
        <div key={kind} className="mt-4">
          <h4 className="text-sm font-semibold tracking-wide text-secondary/70 uppercase">
            {KIND_LABELS[kind] ?? kind}
          </h4>
          <ul className="mt-2 space-y-2">
            {group.map((entity) => (
              <li key={entity.name} className="flex flex-wrap items-center gap-2">
                <span className="font-medium text-secondary">{entity.name}</span>
                {entity.chapters.map((number) => (
                  <a
                    key={number}
                    href={`#capitulo-${number}`}
                    className="rounded-full bg-accent px-2 py-0.5 text-xs text-secondary"
                  >
                    Cap. {number}
                  </a>
                ))}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </section>
  );
}

function DownloadPdf({ novelId, version }: { novelId: string; version: number }) {
  const [unavailable, setUnavailable] = useState(false);

  async function handleClick() {
    const response = await apiFetch(`/api/novels/${novelId}/versions/${version}/pdf`);
    if (response.status === 404) {
      setUnavailable(true);
      return;
    }
    setUnavailable(false);
    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `version-${version}.pdf`;
    link.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div>
      <button
        type="button"
        onClick={() => void handleClick()}
        className="rounded bg-primary px-4 py-2 text-sm font-semibold text-secondary"
      >
        Descargar PDF
      </button>
      {unavailable && (
        <p role="alert" className="mt-2 text-sm break-words">
          El PDF de esta versión aún no está disponible.
        </p>
      )}
    </div>
  );
}

function VersionContent({ novelId, version }: { novelId: string; version: number }) {
  const [load, retry] = useJson<VersionDetail>(`/api/novels/${novelId}/versions/${version}`);
  const [fragment, setFragment] = useState<{ chapter: number; quote: string } | null>(null);
  if (load.status === "loading") return <Loading>Cargando la versión…</Loading>;
  if (load.status === "error") {
    return <LoadError message="No se pudo cargar esa versión." onRetry={retry} />;
  }
  const { view } = load.data;
  return (
    <>
      <Cover view={view} />
      <News changedChapters={view.changed_chapters} />
      <Index chapters={view.chapters} changedChapters={view.changed_chapters} version={version} />
      {view.chapters.map((chapter) => (
        <Chapter
          key={chapter.number}
          chapter={chapter}
          onSelectFragment={(chapterNumber, quote) => setFragment({ chapter: chapterNumber, quote })}
        />
      ))}
      <Ficha entities={view.ficha} />
      <ChangeRequestEntryPoint
        novelId={novelId}
        version={version}
        fragment={fragment}
        onClear={() => setFragment(null)}
      />
    </>
  );
}

function Versions({ novelId }: { novelId: string }) {
  const [load, retry] = useJson<VersionsList>(`/api/novels/${novelId}/versions`);
  const [chosen, setChosen] = useState<number | null>(null);
  if (load.status === "loading") return <Loading>Cargando las versiones…</Loading>;
  if (load.status === "error") {
    return <LoadError message="No se pudo cargar la lista de versiones." onRetry={retry} />;
  }
  const versions = load.data.versions;
  // La vigente es la publicada de número más alto (definitions.md §3); la API las da en orden.
  const shown = chosen ?? versions.at(-1)?.number;
  if (shown === undefined) return <p>Esta novela aún no tiene versiones publicadas.</p>;
  return (
    <>
      <div className="mb-8 flex flex-wrap items-center justify-between gap-3 rounded-lg bg-accent/40 px-4 py-3 sm:px-6">
        <div className="flex items-center gap-2">
          <label htmlFor="reading-version" className="text-sm font-medium text-secondary">
            Versión
          </label>
          <select
            id="reading-version"
            value={shown}
            onChange={(event) => setChosen(Number(event.target.value))}
            className="rounded border border-secondary/30 bg-white px-2 py-1"
          >
            {versions.map((v) => (
              <option key={v.number} value={v.number}>
                v{v.number}
              </option>
            ))}
          </select>
        </div>
        <DownloadPdf key={shown} novelId={novelId} version={shown} />
      </div>
      <VersionContent key={shown} novelId={novelId} version={shown} />
    </>
  );
}

export function ReadingPage() {
  const { novelId = "" } = useParams();
  return (
    <main className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <Versions novelId={novelId} />
    </main>
  );
}
