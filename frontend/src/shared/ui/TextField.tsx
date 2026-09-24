import { useId } from "react";

type TextFieldProps = {
  label: string;
  type: "email" | "password";
  autoComplete: string;
  value: string;
  onChange: (value: string) => void;
  error?: string;
};

export function TextField({ label, type, autoComplete, value, onChange, error }: TextFieldProps) {
  const id = useId();
  const errorId = `${id}-error`;
  return (
    <div className="flex flex-col gap-1">
      <label htmlFor={id}>{label}</label>
      <input
        id={id}
        type={type}
        autoComplete={autoComplete}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        aria-invalid={error ? true : undefined}
        aria-describedby={error ? errorId : undefined}
        className="rounded border border-secondary/30 px-3 py-2"
      />
      {error && (
        <span id={errorId} className="text-sm text-primary">
          {error}
        </span>
      )}
    </div>
  );
}
