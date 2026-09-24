import { useSyncExternalStore } from "react";
import { Navigate, Outlet } from "react-router";

import { clearSession, readSession, subscribeSession } from "../shared/lib";

// Sin sesión guardada la pantalla protegida ni se monta: no llega a pedir datos a la API.
// Si la sesión se borra estando dentro (401, cierre de sesión), se vuelve a acceso.
export function RequireSession() {
  const token = useSyncExternalStore(subscribeSession, readSession);
  if (!token) return <Navigate to="/acceso" replace />;
  return (
    <>
      <div className="flex justify-end px-6 py-2">
        {/* Cerrar sesión es solo local: no hay cierre de sesión en el servidor (§14.3). */}
        <button type="button" onClick={clearSession} className="text-sm underline">
          Cerrar sesión
        </button>
      </div>
      <Outlet />
    </>
  );
}
