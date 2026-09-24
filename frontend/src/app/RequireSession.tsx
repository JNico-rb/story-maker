import { Navigate, Outlet } from "react-router";

import { readSession } from "../shared/lib";

// Sin sesión guardada la pantalla protegida ni se monta: no llega a pedir datos a la API.
export function RequireSession() {
  return readSession() ? <Outlet /> : <Navigate to="/acceso" replace />;
}
