import { BRAND_NAME } from "../../../shared/config";
import { BrandLogo } from "../../../shared/ui";

export function HomePage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl flex-col items-center justify-center gap-6 px-6 text-center">
      <BrandLogo className="h-14 w-auto" />
      <h1 className="text-4xl font-bold tracking-tight text-secondary">{BRAND_NAME}</h1>
      <p className="font-serif text-lg text-muted">Novelas personalizadas para regalar.</p>
      <span className="h-1 w-16 rounded-full bg-primary" aria-hidden="true" />
    </main>
  );
}
