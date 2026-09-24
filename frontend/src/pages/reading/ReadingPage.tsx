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

function LoadError({ message, onRetry }: { message: string; onRetry: () => void }) {
  return (
    <p role="alert" className="mb-6">
      {message}{" "}
      <button type="button" onClick={onRetry} className="underline">
        Reintentar
      </button>
    </p>
  );
}

function Cover({ view }: { view: VersionDetail["view"] }) {
  return (
    <section aria-label="Portada" className="mb-10 text-center">
      <h2 className="font-reading text-3xl font-semibold text-secondary">{view.title}</h2>
      <p className="mt-2">Para {view.recipient}</p>
      <p className="mt-6 font-reading italic">{view.dedication}</p>
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
    <nav aria-label="Índice" className="mb-10">
      <ol className="space-y-1">
        {chapters.map((chapter) => (
          <li key={chapter.number}>
            <a href={`#capitulo-${chapter.number}`}>
              Capítulo {chapter.number}: {chapter.title}
              {changedChapters.includes(chapter.number) && ` — cambiado en v${version}`}
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
    <section aria-label="Novedades" className="mb-10">
      <h3 className="font-reading text-xl font-semibold text-secondary">Novedades</h3>
      <ul className="space-y-1">
        {changedChapters.map((number) => (
          <li key={number}>
            <a href={`#capitulo-${number}`}>Capítulo {number}</a>
          </li>
        ))}
      </ul>
    </section>
  );
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
      className="mb-10"
      onMouseUp={handleMouseUp}
    >
      <h3 className="font-reading text-xl font-semibold text-secondary">{chapter.title}</h3>
      <p className="mt-2">{chapter.text}</p>
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

  if (selection) {
    return (
      <ChangeRequestPanel
        novelId={novelId}
        selection={selection}
        onDiscard={() => {
          setSelection(null);
          onClear();
        }}
      />
    );
  }

  if (!fragment) return null;

  return (
    <button
      type="button"
      onClick={() => setSelection({ type: "fragment", version, chapter: fragment.chapter, quote: fragment.quote })}
      className="mb-6 underline"
    >
      Pedir un cambio
    </button>
  );
}

function Ficha({ entities }: { entities: VersionDetail["view"]["ficha"] }) {
  return (
    <section aria-label="Ficha" className="mb-10">
      <h3 className="font-reading text-xl font-semibold text-secondary">Ficha</h3>
      <ul className="space-y-1">
        {entities.map((entity) => (
          <li key={entity.name}>
            {entity.name}
            {entity.chapters.map((number) => (
              <a key={number} href={`#capitulo-${number}`} className="ml-2">
                capítulo {number}
              </a>
            ))}
          </li>
        ))}
      </ul>
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
    <div className="mb-6">
      <button type="button" onClick={() => void handleClick()} className="underline">
        Descargar PDF
      </button>
      {unavailable && <p role="alert">El PDF de esta versión aún no está disponible.</p>}
    </div>
  );
}

function VersionContent({ novelId, version }: { novelId: string; version: number }) {
  const [load, retry] = useJson<VersionDetail>(`/api/novels/${novelId}/versions/${version}`);
  const [fragment, setFragment] = useState<{ chapter: number; quote: string } | null>(null);
  if (load.status === "loading") return <p>Cargando la versión…</p>;
  if (load.status === "error") {
    return <LoadError message="No se pudo cargar esa versión." onRetry={retry} />;
  }
  const { view } = load.data;
  return (
    <>
      <Cover view={view} />
      <DownloadPdf novelId={novelId} version={version} />
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
  if (load.status === "loading") return <p>Cargando las versiones…</p>;
  if (load.status === "error") {
    return <LoadError message="No se pudo cargar la lista de versiones." onRetry={retry} />;
  }
  const versions = load.data.versions;
  // La vigente es la publicada de número más alto (definitions.md §3); la API las da en orden.
  const shown = chosen ?? versions.at(-1)?.number;
  if (shown === undefined) return <p>Esta novela aún no tiene versiones publicadas.</p>;
  return (
    <>
      <div className="mb-6 flex items-center gap-2">
        <label htmlFor="reading-version">Versión</label>
        <select
          id="reading-version"
          value={shown}
          onChange={(event) => setChosen(Number(event.target.value))}
          className="rounded border border-secondary/30 px-2 py-1"
        >
          {versions.map((v) => (
            <option key={v.number} value={v.number}>
              v{v.number}
            </option>
          ))}
        </select>
      </div>
      <VersionContent key={shown} novelId={novelId} version={shown} />
    </>
  );
}

export function ReadingPage() {
  const { novelId = "" } = useParams();
  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <Versions novelId={novelId} />
    </main>
  );
}
