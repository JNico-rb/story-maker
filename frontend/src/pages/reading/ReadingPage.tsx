import { useEffect, useState } from "react";
import { useParams } from "react-router";

import { apiFetch } from "../../shared/api";
import type { components } from "../../shared/api/schema";

type VersionsList = components["schemas"]["VersionsListResponse"];
type VersionDetail = components["schemas"]["VersionDetailResponse"];
type Load<T> = { status: "loading" } | { status: "ready"; data: T };

// Cada carga vive en un componente con `key`: cambiar de versión lo desmonta y la respuesta
// tardía de la anterior se descarta, así nunca se mezclan dos versiones (026-I1).
function useJson<T>(path: string): Load<T> {
  const [load, setLoad] = useState<Load<T>>({ status: "loading" });
  useEffect(() => {
    let current = true;
    void apiFetch(path)
      .then((response) => response.json() as Promise<T>)
      .then((data) => {
        if (current) setLoad({ status: "ready", data });
      });
    return () => {
      current = false;
    };
  }, [path]);
  return load;
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

function VersionContent({ novelId, version }: { novelId: string; version: number }) {
  const load = useJson<VersionDetail>(`/api/novels/${novelId}/versions/${version}`);
  if (load.status === "loading") return <p>Cargando la versión…</p>;
  return <Cover view={load.data.view} />;
}

function Versions({ novelId }: { novelId: string }) {
  const load = useJson<VersionsList>(`/api/novels/${novelId}/versions`);
  const [chosen, setChosen] = useState<number | null>(null);
  if (load.status === "loading") return <p>Cargando las versiones…</p>;
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
