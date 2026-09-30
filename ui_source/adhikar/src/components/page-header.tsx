export function PageHeader({
  eyebrow,
  title,
  description,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
}) {
  return (
    <header className="mb-12 max-w-2xl">
      {eyebrow && (
        <p className="mb-4 text-sm font-medium uppercase tracking-[0.14em] text-accent">
          {eyebrow}
        </p>
      )}
      <h1 className="font-display text-[2.25rem] leading-[1.1] sm:text-[3rem]">{title}</h1>
      {description && (
        <p className="mt-4 text-lg leading-relaxed text-muted-foreground">{description}</p>
      )}
    </header>
  );
}
