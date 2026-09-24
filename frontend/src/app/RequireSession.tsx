import { useSyncExternalStore } from "react";
import { Navigate, Outlet } from "react-router";

import { readSession, subscribeSession } from "../shared/lib";

// Sin sesión guardada la pantalla protegida ni se monta: no llega a pedir datos a la API.
// Si la sesión se borra estando dentro (401, cierre de sesión), se vuelve a acceso.
export function RequireSession() {
  const token = useSyncExternalStore(subscribeSession, readSession);
  return token ? <Outlet /> : <Navigate to="/acceso" replace />;
}
