import { Outlet } from "react-router";

import { AppHeader } from "../shared/ui";

export function BrandLayout() {
  return (
    <>
      <AppHeader />
      <Outlet />
    </>
  );
}
