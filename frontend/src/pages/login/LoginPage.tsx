import { useState, type FormEvent } from "react";
import { Link, useLocation, useNavigate } from "react-router";

import { invalidFields } from "../../shared/api";
import { saveSession } from "../../shared/lib";
import { TextField } from "../../shared/ui";

type ArrivalState = { registeredEmail?: string } | null;
type FieldErrors = { email?: string; password?: string };

// El acceso no revela las reglas del registro (spec 002): sus mensajes no dan límites.
async function errorsFor(response: Response): Promise<FieldErrors> {
  const fields = await invalidFields(response);
  return {
    email: fields.has("email") ? "Revisa el email." : undefined,
    password: fields.has("password") ? "Revisa la contraseña." : undefined,
  };
}

export function LoginPage() {
  const navigate = useNavigate();
  const arrival = useLocation().state as ArrivalState;
  const [email, setEmail] = useState(arrival?.registeredEmail ?? "");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<FieldErrors>({});

  async function submit(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    setPassword("");
    if (response.ok) {
      const { access_token } = (await response.json()) as { access_token: string };
      saveSession(access_token);
      await navigate("/");
    } else {
      setErrors(await errorsFor(response));
    }
  }

  return (
    <main className="mx-auto max-w-sm px-6 py-10">
      <h2 className="mb-6 text-xl font-semibold text-secondary">Entrar</h2>
      {arrival?.registeredEmail && (
        <p role="status" className="mb-4 rounded bg-accent px-3 py-2">
          Cuenta creada. Ya puedes entrar.
        </p>
      )}
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
          autoComplete="current-password"
          value={password}
          onChange={setPassword}
          error={errors.password}
        />
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
