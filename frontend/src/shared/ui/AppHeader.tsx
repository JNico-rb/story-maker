import { BRAND_NAME } from "../config";
import { BrandLogo } from "./BrandLogo";

export function AppHeader() {
  return (
    <header className="flex items-center gap-3 border-b border-secondary/10 px-4 py-3 sm:gap-4 sm:px-6 sm:py-4">
      <BrandLogo className="h-8 w-auto sm:h-10" />
      <h1 className="text-lg font-semibold tracking-tight text-secondary sm:text-2xl">{BRAND_NAME}</h1>
    </header>
  );
}
