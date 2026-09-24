import { createBrowserRouter, type RouteObject } from "react-router";

import { AppHeader } from "../shared/ui";

// Mientras no haya pantallas, la ruta raíz muestra la cabecera de marca (spec 000).
export const routes: RouteObject[] = [{ path: "/", element: <AppHeader /> }];

export const router = createBrowserRouter(routes);
