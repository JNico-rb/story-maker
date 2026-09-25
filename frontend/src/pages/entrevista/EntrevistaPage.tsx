import { useEffect, useState } from "react";
import { useParams } from "react-router";

import { apiFetch, errorMessage } from "../../shared/api";

// Modelo del backend (008-brief-y-entrevista); `schema.d.ts` no lo tiene todavía (024, alcance),
// así que se declara aquí igual, sin inventar campos.
type InterviewMessage = { author: "user" | "interviewer"; text: string };

type BriefContent = {
  recipient: { name: string; age: number | null; birth_date: string | null; traits: unknown[]; relation: string | null };
  close_ones: unknown[];
  recollections: unknown[];
  occasion: string | null;
  genre: string | null;
  tone: string | null;
  length: string | null;
  dedication: string;
  banned_asked: boolean;
  plot_wishes: unknown[];
};

type Contradiccion = { rule: string; fields: string[]; detail?: Record<string, string> | null };
type SchemaError = { message: string; fields: string[] };
type VerifiedFact = {
  id: number;
  subject: string;
  attribute: string;
  value: string;
  quote: string;
  accepted: boolean | null;
  mandatory: boolean;
};

type BriefOut = {
  status: "draft" | "confirmed";
  content: BriefContent;
  missing_fields: string[];
  contradictions: Contradiccion[];
  schema_errors: SchemaError[];
  mandatory_count: number;
  max_mandatory_elements: number;
  personal_elements: unknown[];
  verified_facts: VerifiedFact[];
};

type Load<T> = { status: "loading" } | { status: "ready"; data: T } | { status: "error" };

// Además de cargar, entrega un actualizador directo: los turnos, los textos libres y la
// confirmación devuelven el brief ya recalculado, y esta pantalla nunca lo recalcula por su
// cuenta (024-I1) — solo sustituye el que ya tenía por el que trae la respuesta.
function useJson<T>(path: string): [Load<T>, (updater: (data: T) => T) => void] {
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
  }, [path]);
  const update = (updater: (data: T) => T) => {
    setLoad((current) => (current.status === "ready" ? { status: "ready", data: updater(current.data) } : current));
  };
  return [load, update];
}

function Chat({
  novelId,
  messages,
  addMessages,
  readOnly,
  onBrief,
}: {
  novelId: string;
  messages: InterviewMessage[];
  addMessages: (update: (current: InterviewMessage[]) => InterviewMessage[]) => void;
  readOnly: boolean;
  onBrief: (brief: BriefOut) => void;
}) {
  const [text, setText] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (text.trim() === "" || submitting) return;
    setSubmitting(true);
    setError(undefined);
    const response = await apiFetch(`/api/novels/${novelId}/interview/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text }),
    });
    if (response.ok) {
      const turn = (await response.json()) as { reply: string; brief: BriefOut };
      addMessages((current) => [...current, { author: "user", text }, { author: "interviewer", text: turn.reply }]);
      onBrief(turn.brief);
      setText("");
      setSubmitting(false);
      return;
    }
    setSubmitting(false);
    setError(await errorMessage(response));
  }

  return (
    <section aria-label="Chat" className="mb-10">
      {messages.length > 0 && (
        <ul aria-label="Historial" className="mb-4 space-y-2">
          {messages.map((message, index) => (
            <li key={index} className={message.author === "user" ? "text-right" : "text-left"}>
              {message.text}
            </li>
          ))}
        </ul>
      )}
      {!readOnly && (
        <form
          aria-label="Entrevista"
          onSubmit={(event) => void handleSubmit(event)}
          className="flex flex-wrap items-end gap-3"
        >
          <label htmlFor="entrevista-mensaje" className="sr-only">
            Mensaje
          </label>
          <input
            id="entrevista-mensaje"
            aria-label="Mensaje"
            value={text}
            onChange={(event) => setText(event.target.value)}
            className="min-w-64 flex-1 rounded border border-secondary/30 p-2"
          />
          <button
            type="submit"
            disabled={text.trim() === "" || submitting}
            className="rounded bg-primary px-4 py-2 text-sm font-semibold text-secondary disabled:opacity-50"
          >
            Enviar
          </button>
        </form>
      )}
      {error && (
        <p role="alert" className="mt-3 rounded bg-accent px-3 py-2 text-sm">
          {error}
        </p>
      )}
    </section>
  );
}

function BriefPanel({ brief }: { brief: BriefOut }) {
  const fixed: [string, string][] = [];
  if (brief.content.recipient.name) fixed.push(["Nombre", brief.content.recipient.name]);
  if (brief.content.occasion) fixed.push(["Ocasión", brief.content.occasion]);
  if (brief.content.genre) fixed.push(["Género", brief.content.genre]);
  if (brief.content.tone) fixed.push(["Tono", brief.content.tone]);
  if (brief.content.length) fixed.push(["Extensión", brief.content.length]);
  if (brief.content.dedication) fixed.push(["Dedicatoria", brief.content.dedication]);

  return (
    <section aria-label="Brief" className="mb-10 rounded-lg border border-secondary/10 bg-white/60 p-5">
      {fixed.length === 0 ? (
        <p>Todavía no hay nada fijado.</p>
      ) : (
        <dl aria-label="Fijado" className="space-y-1">
          {fixed.map(([label, value]) => (
            <div key={label} className="flex gap-2">
              <dt className="font-semibold text-secondary">{label}:</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}
      {brief.missing_fields.length > 0 && (
        <ul aria-label="Faltantes" className="mt-3 list-disc pl-5 text-sm text-secondary/70">
          {brief.missing_fields.map((field) => (
            <li key={field}>Falta: {field}</li>
          ))}
        </ul>
      )}
      {brief.contradictions.length > 0 && (
        <ul aria-label="Contradicciones" className="mt-3 list-disc pl-5 text-sm text-secondary/70">
          {brief.contradictions.map((item, index) => (
            <li key={index}>
              Contradicción {item.rule}: {item.fields.join(", ")}
            </li>
          ))}
        </ul>
      )}
      <p className="mt-3 text-sm text-secondary/70">
        Obligatorios: {brief.mandatory_count}/{brief.max_mandatory_elements}
      </p>
    </section>
  );
}

// Un hecho pendiente de decisión ofrece aceptar o rechazar (024-C07); decidido, deja de
// ofrecerlas (024-C08). Marcar obligatorio no se oculta según el estado de aceptación: el
// servidor es quien decide si aplica (024-C09, 024-I1).
function FactRow({
  novelId,
  fact,
  onBrief,
  readOnly,
}: {
  novelId: string;
  fact: VerifiedFact;
  onBrief: (updater: (brief: BriefOut) => BriefOut) => void;
  readOnly: boolean;
}) {
  const [error, setError] = useState<string>();

  async function patch(body: { accepted?: boolean; mandatory?: boolean }) {
    const response = await apiFetch(`/api/novels/${novelId}/brief/extracted-facts/${fact.id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (response.ok) {
      const brief = (await response.json()) as BriefOut;
      onBrief(() => brief);
      setError(undefined);
      return;
    }
    setError(await errorMessage(response));
  }

  return (
    <li className="flex flex-wrap items-center gap-x-3 gap-y-1 py-2">
      <span>
        {fact.subject} · {fact.attribute}: {fact.value}
      </span>
      {fact.accepted === null && !readOnly && (
        <>
          <button type="button" onClick={() => void patch({ accepted: true })} className="text-sm underline">
            Aceptar
          </button>
          <button type="button" onClick={() => void patch({ accepted: false })} className="text-sm underline">
            Rechazar
          </button>
        </>
      )}
      {fact.accepted === true && <span className="text-sm text-secondary/70">Aceptado</span>}
      {fact.accepted === false && <span className="text-sm text-secondary/70">Rechazado</span>}
      <label className="flex items-center gap-1 text-sm">
        <input
          type="checkbox"
          aria-label="Obligatorio"
          checked={fact.mandatory}
          disabled={readOnly}
          onChange={() => void patch({ mandatory: !fact.mandatory })}
        />
        Obligatorio
      </label>
      {error && (
        <p role="alert" className="w-full text-sm">
          {error}
        </p>
      )}
    </li>
  );
}

function FreeTextForm({
  novelId,
  onFacts,
  readOnly,
}: {
  novelId: string;
  onFacts: (facts: VerifiedFact[]) => void;
  readOnly: boolean;
}) {
  const [content, setContent] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string>();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (content.trim() === "" || submitting) return;
    setSubmitting(true);
    setError(undefined);
    const response = await apiFetch(`/api/novels/${novelId}/free-texts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content }),
    });
    if (response.status === 201) {
      const created = (await response.json()) as { free_text_id: number; verified_facts: VerifiedFact[] };
      onFacts(created.verified_facts);
      setContent("");
      setSubmitting(false);
      return;
    }
    setSubmitting(false);
    setError(await errorMessage(response));
  }

  if (readOnly) return null;

  return (
    <form onSubmit={(event) => void handleSubmit(event)} className="flex flex-wrap items-end gap-3">
      <label htmlFor="entrevista-texto-libre" className="sr-only">
        Texto libre
      </label>
      <textarea
        id="entrevista-texto-libre"
        aria-label="Texto libre"
        value={content}
        onChange={(event) => setContent(event.target.value)}
        className="min-w-64 flex-1 rounded border border-secondary/30 p-2"
      />
      <button
        type="submit"
        disabled={content.trim() === "" || submitting}
        className="rounded bg-primary px-4 py-2 text-sm font-semibold text-secondary disabled:opacity-50"
      >
        Enviar texto
      </button>
      {error && (
        <p role="alert" className="w-full text-sm">
          {error}
        </p>
      )}
    </form>
  );
}

function FreeTextAndFacts({
  novelId,
  brief,
  updateBrief,
  readOnly,
}: {
  novelId: string;
  brief: BriefOut;
  updateBrief: (updater: (brief: BriefOut) => BriefOut) => void;
  readOnly: boolean;
}) {
  return (
    <section aria-label="Texto libre y hechos" className="mb-10">
      <FreeTextForm
        novelId={novelId}
        readOnly={readOnly}
        onFacts={(facts) => updateBrief((current) => ({ ...current, verified_facts: [...current.verified_facts, ...facts] }))}
      />
      {brief.verified_facts.length > 0 && (
        <ul aria-label="Hechos" className="mt-4 divide-y divide-secondary/10">
          {brief.verified_facts.map((fact) => (
            <FactRow key={fact.id} novelId={novelId} fact={fact} onBrief={updateBrief} readOnly={readOnly} />
          ))}
        </ul>
      )}
    </section>
  );
}

export function EntrevistaPage() {
  const { novelId = "" } = useParams();
  const [messagesLoad, addMessages] = useJson<InterviewMessage[]>(`/api/novels/${novelId}/interview/messages`);
  const [briefLoad, updateBrief] = useJson<BriefOut>(`/api/novels/${novelId}/brief`);

  if (messagesLoad.status === "loading" || briefLoad.status === "loading") {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p role="status">Cargando la entrevista…</p>
      </main>
    );
  }
  if (messagesLoad.status === "error" || briefLoad.status === "error") {
    return (
      <main className="mx-auto max-w-3xl px-6 py-10">
        <p role="alert">No se pudo cargar la entrevista.</p>
      </main>
    );
  }

  const brief = briefLoad.data;
  const readOnly = brief.status === "confirmed";

  return (
    <main className="mx-auto max-w-3xl px-6 py-10">
      <h2 className="mb-6 text-xl font-semibold text-secondary">Entrevista</h2>
      <BriefPanel brief={brief} />
      <FreeTextAndFacts novelId={novelId} brief={brief} updateBrief={updateBrief} readOnly={readOnly} />
      <Chat
        novelId={novelId}
        messages={messagesLoad.data}
        addMessages={addMessages}
        readOnly={readOnly}
        onBrief={(newBrief) => updateBrief(() => newBrief)}
      />
    </main>
  );
}
