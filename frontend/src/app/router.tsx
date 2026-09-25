import { createBrowserRouter, type RouteObject } from "react-router";

import { ChapterEditorPage } from "../pages/chapter-editor";
import { EntrevistaPage } from "../pages/entrevista";
import { LoginPage } from "../pages/login";
import { NovelsPage } from "../pages/novels";
import { ProgresoPage } from "../pages/progreso";
import { ReadingPage } from "../pages/reading";
import { RegisterPage } from "../pages/register";
import { BrandLayout } from "./BrandLayout";
import { RequireSession } from "./RequireSession";

// Pantallas que exigen sesión; cada spec de pantalla añade la suya. `extra` sirve a las pruebas.
const protectedScreens: RouteObject[] = [
  { path: "/", element: <NovelsPage /> },
  { path: "/novelas/:novelId/entrevista", element: <EntrevistaPage /> },
  { path: "/novelas/:novelId/progreso", element: <ProgresoPage /> },
  { path: "/novelas/:novelId/lectura", element: <ReadingPage /> },
  { path: "/novelas/:novelId/versiones/:version/capitulos/:chapterNumber/editar", element: <ChapterEditorPage /> },
];

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
