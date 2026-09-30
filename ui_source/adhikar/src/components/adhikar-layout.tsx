import { useState } from "react";
import { Link } from "@tanstack/react-router";
import { Globe, Menu } from "lucide-react";
import { useLanguage } from "@/components/language-provider";
import { AdhikarMark } from "@/components/adhikar-mark";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
import { LANGUAGES, type LanguageCode } from "@/lib/i18n";

export function AdhikarLayout({ children }: { children: React.ReactNode }) {
  const { t, language, setLanguage, rtl } = useLanguage();
  const [open, setOpen] = useState(false);

  const links = [
    { to: "/advisor", label: t("nav.advisor") },
    { to: "/nearby", label: t("nav.nearby") },
    { to: "/about", label: t("nav.about") },
  ];

  const languageSelect = (id: string, className?: string) => (
    <div className={className}>
      <label className="sr-only" htmlFor={id}>
        {t("lang.label")}
      </label>
      <Select value={language} onValueChange={(value) => setLanguage(value as LanguageCode)}>
        <SelectTrigger id={id} className="h-10 w-full min-w-[9.5rem] gap-2">
          <Globe className="size-4 opacity-70" aria-hidden="true" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {LANGUAGES.map((option) => (
            <SelectItem key={option.code} value={option.code}>
              {option.nativeName}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );

  return (
    <div className="flex min-h-dvh flex-col bg-background" dir={rtl ? "rtl" : "ltr"}>
      <header className="sticky top-0 z-40 border-b border-border bg-background">
        <div className="mx-auto flex h-16 w-full max-w-6xl items-center gap-4 px-5 sm:px-8">
          <Link
            to="/"
            className="flex min-w-0 items-center gap-2.5 rounded-md outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-background"
          >
            <AdhikarMark className="size-8 shrink-0 text-primary" />
            <Wordmark className="truncate" />
          </Link>

          <nav className="ms-8 hidden items-center gap-6 md:flex" aria-label="Main">
            {links.map((link) => (
              <HeaderLink key={link.to} to={link.to} label={link.label} />
            ))}
          </nav>

          <div className="ms-auto flex items-center gap-2">
            {languageSelect("language-select", "hidden lg:block")}
            <Button asChild className="hidden md:inline-flex">
              <Link to="/advisor">{t("form.submit")}</Link>
            </Button>

            <Sheet open={open} onOpenChange={setOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="outline"
                  size="icon"
                  aria-label="Open menu"
                  className="min-h-11 min-w-11 md:hidden"
                >
                  <Menu className="size-5" aria-hidden="true" />
                </Button>
              </SheetTrigger>
              <SheetContent side={rtl ? "left" : "right"} className="w-[18rem] p-6">
                <SheetHeader className="p-0 text-start">
                  <SheetTitle className="flex items-center gap-2.5 font-display text-2xl font-normal">
                     <AdhikarMark className="size-7 text-primary" />
                     <Wordmark />
                  </SheetTitle>
                </SheetHeader>
                <nav className="mt-8 flex flex-col" aria-label="Mobile">
                  {links.map((link) => (
                    <Link
                      key={link.to}
                      to={link.to}
                      onClick={() => setOpen(false)}
                      className="border-b border-border py-3.5 text-base transition-colors hover:text-primary"
                      activeProps={{ className: "font-medium text-primary" }}
                    >
                      {link.label}
                    </Link>
                  ))}
                </nav>
                <div className="mt-6">{languageSelect("language-select-mobile")}</div>
                <Button asChild className="mt-4 w-full" onClick={() => setOpen(false)}>
                  <Link to="/advisor">{t("form.submit")}</Link>
                </Button>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-5 py-12 sm:px-8 sm:py-16">
        {children}
      </main>

      <footer className="border-t border-border">
        <div className="mx-auto w-full max-w-6xl px-5 py-14 sm:px-8 sm:py-16">
          <div className="flex flex-col gap-12 md:flex-row md:justify-between">
            <div className="max-w-sm">
              <div className="flex items-center gap-2.5">
                <AdhikarMark className="size-7 text-primary" />
                <Wordmark />
              </div>
              <p className="mt-3 text-[0.9375rem] leading-relaxed text-muted-foreground">
                Making government scheme information easier to find, understand, and navigate.
              </p>
            </div>

            <nav className="flex flex-col gap-2.5 text-sm" aria-label="Footer">
              {links.map((link) => (
                <Link
                  key={link.to}
                  to={link.to}
                  className="text-muted-foreground transition-colors hover:text-foreground"
                >
                  {link.label}
                </Link>
              ))}
              <a
                className="text-muted-foreground transition-colors hover:text-foreground"
                href="https://www.myscheme.gov.in/"
                target="_blank"
                rel="noreferrer noopener"
              >
                myscheme.gov.in
              </a>
            </nav>
          </div>

          <p className="mt-12 border-t border-border pt-7 text-[0.9375rem] leading-relaxed text-muted-foreground">
            <DisclaimerWithLink text={t("disclaimer.long")} />
          </p>
        </div>
      </footer>
    </div>
  );
}

function Wordmark({ className }: { className?: string }) {
  return (
    <span className={`flex min-w-0 flex-col leading-none ${className ?? ""}`}>
      <span className="font-display text-[1.65rem] text-primary">Adhikar</span>
      <span className="mt-1 text-[0.58rem] font-medium uppercase tracking-[0.22em] text-muted-foreground">INDIA</span>
    </span>
  );
}

function HeaderLink({ to, label }: { to: string; label: string }) {
  return (
    <Link
      to={to}
      className="border-b-2 border-transparent py-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
      activeProps={{ className: "border-accent text-foreground font-medium" }}
    >
      {label}
    </Link>
  );
}

function DisclaimerWithLink({ text }: { text: string }) {
  const parts = text.split("myScheme");
  if (parts.length === 1) return <>{text}</>;
  return (
    <>
      {parts[0]}
      <a
        href="https://www.myscheme.gov.in/"
        target="_blank"
        rel="noreferrer noopener"
        className="underline underline-offset-2 transition-colors hover:text-foreground"
      >
        myScheme
      </a>
      {parts.slice(1).join("myScheme")}
    </>
  );
}
