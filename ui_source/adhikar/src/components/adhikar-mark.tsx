type Props = {
  className?: string;
  title?: string;
};

/** Adhikar mark: an open A-shaped doorway and a restrained path forward. */
export function AdhikarMark({ className, title }: Props) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      className={className}
      role={title ? "img" : "presentation"}
      aria-hidden={title ? undefined : true}
      aria-label={title}
    >
      {title ? <title>{title}</title> : null}
      <path d="M6.5 26 15.9 5.2 25.5 26" stroke="currentColor" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M11.1 17.7h9.5" stroke="currentColor" strokeWidth="2.3" strokeLinecap="round" />
      <path d="M15.9 21.5v4.2" stroke="var(--accent)" strokeWidth="2.3" strokeLinecap="round" />
    </svg>
  );
}
