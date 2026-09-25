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
