import { createFileRoute, Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";
import { AdhikarLayout } from "@/components/adhikar-layout";
import { Reveal } from "@/components/reveal";
import { useLanguage } from "@/components/language-provider";
import heroPhoto from "@/assets/adhikar-hero.jpg";

const STEPS = [
  {
    title: "Tell us about yourself",
    body: "Answer a few optional questions about your situation. Skip anything you would rather not share.",
  },
  {
    title: "Discover relevant schemes",
    body: "Adhikar uses your answers to surface government schemes that may be relevant to you.",
  },
  {
    title: "Understand your options",
    body: "Review requirements, benefits and next steps, then verify everything with the official source.",
  },
];

export const Route = createFileRoute("/")({
  head: () => ({
    meta: [
      { title: "Adhikar — Government support, made easier to find" },
      {
        name: "description",
        content:
          "A private, multilingual helper that pre-screens Indian government schemes, explains them in simple words, and points you to official sources.",
      },
      { property: "og:title", content: "Adhikar — Government support, in your language" },
      {
        property: "og:description",
        content:
          "Answer a few optional questions and see which Indian government schemes are worth checking, in 13 languages, with voice support.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary_large_image" },
    ],
  }),
  component: HomePage,
});

function HomePage() {
  const { t } = useLanguage();

  return (
    <AdhikarLayout>
      {/* Hero */}
      <section className="grid items-center gap-12 lg:grid-cols-[1.05fr_1fr] lg:gap-16">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.14em] text-accent">
            13 languages · voice supported
          </p>
          <h1 className="mt-5 font-display text-[2.5rem] leading-[1.08] sm:text-[3.5rem]">
            Find government support that may be right for you.
          </h1>
          <p className="mt-6 max-w-xl text-lg leading-relaxed text-muted-foreground">
            Answer a few simple questions and discover schemes that may match your situation, in your
            language.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Button asChild size="lg">
              <Link to="/advisor">Find my schemes →</Link>
            </Button>
            <Button asChild size="lg" variant="outline">
              <a href="#how-it-works">How it works</a>
            </Button>
          </div>
        </div>

        <figure className="m-0">
          <img
            src={heroPhoto}
            alt="Members of a rural women's self-help group sitting together during a village meeting in Tamil Nadu, India"
            width={1600}
            height={1100}
            className="aspect-[16/11] w-full rounded-xl border border-border object-cover object-center"
          />
          <figcaption className="mt-2 text-xs text-muted-foreground">
            Photo:{" "}
            <a
              href="https://commons.wikimedia.org/wiki/File:India_-_Faces_-_Rural_women_driving_their_own_change_1_(2229752965).jpg"
              target="_blank"
              rel="noreferrer noopener"
              className="underline underline-offset-2 hover:text-foreground"
            >
              McKay Savage
            </a>
            , CC BY 2.0
          </figcaption>
        </figure>
      </section>

      {/* Why Adhikar */}
      <Reveal as="section" className="mt-24 max-w-3xl sm:mt-28">
        <p className="text-sm font-medium uppercase tracking-[0.14em] text-accent">Why Adhikar</p>
        <h2 className="mt-4 font-display text-3xl sm:text-[2.5rem]">
          Government support should not be hard to find.
        </h2>
        <p className="mt-4 text-lg leading-relaxed text-muted-foreground">
          Information about welfare is often scattered across websites, languages and complicated
          procedures. Adhikar brings it together in one simpler place, helping people discover support
          that may be relevant to them.
        </p>
      </Reveal>

      {/* How it works */}
      <section id="how-it-works" className="mt-24 scroll-mt-24 sm:mt-28">
        <h2 className="font-display text-3xl sm:text-[2.25rem]">How it works</h2>
        <ol className="mt-12 grid gap-12 md:grid-cols-3 md:gap-12">
          {STEPS.map((step, index) => (
            <li key={step.title} className="border-t border-border pt-5">
              <span className="font-display text-2xl text-accent">
                {String(index + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-2 text-lg font-semibold">{step.title}</h3>
              <p className="mt-2 leading-relaxed text-muted-foreground">{step.body}</p>
            </li>
          ))}
        </ol>
      </section>

      {/* Social impact */}
      <section className="mt-24 border-t border-border pt-14 sm:mt-28 sm:pt-16">
        <p className="text-sm font-medium uppercase tracking-[0.14em] text-accent">Social impact</p>
        <h2 className="mt-4 font-display text-3xl sm:text-[2.25rem]">Making welfare information easier to access.</h2>
        <div className="mt-10 grid gap-12 md:grid-cols-3 md:gap-12">
          {[{ title: "Access", body: "Find support in a language you understand." }, { title: "Clarity", body: "Understand what a scheme offers, what it requires, and what to do next." }, { title: "Community", body: "Help bring awareness and digital guidance closer to people who need it." }].map((item) => (
            <div key={item.title} className="border-t border-border pt-5">
              <h3 className="text-sm font-semibold uppercase tracking-[0.12em]">{item.title}</h3>
              <p className="mt-2 leading-relaxed text-muted-foreground">{item.body}</p>
            </div>
          ))}
        </div>
      </section>

      <Reveal as="section" className="mt-24 border-y border-border py-16 sm:mt-28 sm:py-24">
        <p className="max-w-4xl font-display text-4xl leading-[1.08] sm:text-6xl">
          Every Indian family should be able to understand what support may be available to them.
        </p>
      </Reveal>

      {/* Privacy */}
      <section className="mt-24 grid gap-8 border-t border-border pt-14 sm:mt-28 sm:pt-16 lg:grid-cols-[1.1fr_1fr] lg:gap-16">
        <div>
          <p className="text-sm font-medium uppercase tracking-[0.14em] text-accent">Your privacy comes first</p>
          <h2 className="mt-4 max-w-2xl font-display text-2xl leading-snug sm:text-3xl">
            Adhikar does not require an account or Aadhaar.
          </h2>
          <p className="mt-3 max-w-xl leading-relaxed text-muted-foreground">
            Questions are optional, and you should never share sensitive information such as Aadhaar,
            bank or card numbers.
          </p>
        </div>

        <ul className="space-y-4 self-center">
          {["consent.point1", "consent.point2", "consent.point3"].map((key) => (
            <li key={key} className="flex gap-3 leading-relaxed text-muted-foreground">
              <span aria-hidden="true" className="mt-2.5 size-1.5 shrink-0 rounded-full bg-accent" />
              <span>{t(key as "consent.point1")}</span>
            </li>
          ))}
        </ul>
      </section>
    </AdhikarLayout>
  );
}
