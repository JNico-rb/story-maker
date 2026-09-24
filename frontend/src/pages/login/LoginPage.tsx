import { useState } from "react";
import { Link, useLocation } from "react-router";

type ArrivalState = { registeredEmail?: string } | null;

export function LoginPage() {
  const arrival = useLocation().state as ArrivalState;
  const [email, setEmail] = useState(arrival?.registeredEmail ?? "");
  const [password, setPassword] = useState("");

  return (
    <main className="mx-auto max-w-sm px-6 py-10">
      <h2 className="mb-6 text-xl font-semibold text-secondary">Entrar</h2>
      {arrival?.registeredEmail && (
        <p role="status" className="mb-4 rounded bg-accent px-3 py-2">
          Cuenta creada. Ya puedes entrar.
        </p>
      )}
      <form noValidate className="flex flex-col gap-4">
        <label className="flex flex-col gap-1">
          Email
          <input
            type="email"
            autoComplete="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            className="rounded border border-secondary/30 px-3 py-2"
          />
        </label>
        <label className="flex flex-col gap-1">
          Contraseña
          <input
            type="password"
            autoComplete="current-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="rounded border border-secondary/30 px-3 py-2"
          />
        </label>
        <button type="submit" className="rounded bg-primary px-4 py-2 font-semibold text-secondary">
          Entrar
        </button>
      </form>
      <p className="mt-6 text-sm">
        ¿No tienes cuenta? <Link to="/registro" className="underline">Crear cuenta</Link>
      </p>
    </main>
  );
}
