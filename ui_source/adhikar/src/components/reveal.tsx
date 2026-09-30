import { motion, useReducedMotion } from "framer-motion";
import type { ReactNode } from "react";

/** Fades and slides content into view once, subtly. */
export function Reveal({
  children,
  delay = 0,
  className,
  as = "div",
}: {
  children: ReactNode;
  delay?: number;
  className?: string;
  as?: "div" | "section" | "li";
}) {
  const reduced = useReducedMotion();
  const Comp = motion[as];

  if (reduced) {
    return <Comp className={className}>{children}</Comp>;
  }

  return (
    <Comp
      className={className}
      initial={{ opacity: 0, y: 16 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true, amount: 0.15 }}
      transition={{ duration: 0.45, delay, ease: [0.22, 1, 0.36, 1] }}
    >
      {children}
    </Comp>
  );
}
