import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

export function RegisterPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  async function submit(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    setPassword("");
    if (response.status === 201) {
      await navigate("/acceso", { state: { registeredEmail: email } });
    }
  }

  return (
    <main className="mx-auto max-w-sm px-6 py-10">
      <h2 className="mb-6 text-xl font-semibold text-secondary">Crear cuenta</h2>
      <form noValidate onSubmit={(event) => void submit(event)} className="flex flex-col gap-4">
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
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            className="rounded border border-secondary/30 px-3 py-2"
          />
        </label>
        <button type="submit" className="rounded bg-primary px-4 py-2 font-semibold text-secondary">
          Crear cuenta
        </button>
      </form>
      <p className="mt-6 text-sm">
        ¿Ya tienes cuenta? <Link to="/acceso" className="underline">Entrar</Link>
      </p>
    </main>
  );
}
