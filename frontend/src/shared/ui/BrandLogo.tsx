import logoUrl from "./assets/qaracter-logo.png";

export function BrandLogo({ className }: { className?: string }) {
  return <img src={logoUrl} alt="Qaracter" className={className} />;
}
