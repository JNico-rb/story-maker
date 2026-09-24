import { createBrowserRouter, type RouteObject } from "react-router";

import { LoginPage } from "../pages/login";
import { RegisterPage } from "../pages/register";
import { BrandLayout } from "./BrandLayout";

export function buildRoutes(): RouteObject[] {
  return [
    {
      element: <BrandLayout />,
      children: [
        { path: "/", element: null },
        { path: "/acceso", element: <LoginPage /> },
        { path: "/registro", element: <RegisterPage /> },
      ],
    },
  ];
}

export const routes = buildRoutes();

export const router = createBrowserRouter(routes);
