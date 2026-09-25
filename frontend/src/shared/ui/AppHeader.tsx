import { BRAND_NAME } from "../config";
import { BrandLogo } from "./BrandLogo";

export function AppHeader() {
  return (
    <header className="flex items-center gap-4 border-b border-secondary/10 px-6 py-4">
      <BrandLogo className="h-10 w-auto" />
      <h1 className="text-2xl font-semibold tracking-tight text-secondary">{BRAND_NAME}</h1>
    </header>
  );
}
