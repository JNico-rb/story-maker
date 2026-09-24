import { createBrowserRouter, type RouteObject } from "react-router";

import { LoginPage } from "../pages/login";
import { RegisterPage } from "../pages/register";
import { BrandLayout } from "./BrandLayout";
import { RequireSession } from "./RequireSession";

// Pantallas que exigen sesión; cada spec de pantalla añade la suya. `extra` sirve a las pruebas.
const protectedScreens: RouteObject[] = [{ path: "/", element: null }];

export function buildRoutes(extra: RouteObject[] = []): RouteObject[] {
  return [
    {
      element: <BrandLayout />,
      children: [
        { element: <RequireSession />, children: [...protectedScreens, ...extra] },
        { path: "/acceso", element: <LoginPage /> },
        { path: "/registro", element: <RegisterPage /> },
      ],
    },
  ];
}

export const routes = buildRoutes();

export const router = createBrowserRouter(routes);
