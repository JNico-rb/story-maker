import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router";

import { TextField } from "../../shared/ui";

type FieldErrors = { email?: string };

export function RegisterPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});

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
    } else if (response.status === 409) {
      setErrors({ email: "Ese email ya tiene cuenta." });
    }
  }

  return (
    <main className="mx-auto max-w-sm px-6 py-10">
      <h2 className="mb-6 text-xl font-semibold text-secondary">Crear cuenta</h2>
      <form noValidate onSubmit={(event) => void submit(event)} className="flex flex-col gap-4">
        <TextField
          label="Email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={setEmail}
          error={errors.email}
        />
        <TextField
          label="Contraseña"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={setPassword}
        />
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
