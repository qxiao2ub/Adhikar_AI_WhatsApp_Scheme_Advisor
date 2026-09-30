import { createFileRoute } from "@tanstack/react-router";
import { AdhikarLayout } from "@/components/adhikar-layout";
import { PageHeader } from "@/components/page-header";

export const Route = createFileRoute("/about")({
  head: () => ({
    meta: [
      { title: "How Adhikar works — transparent scheme discovery" },
      {
        name: "description",
        content:
          "How Adhikar pre-screens Indian government schemes: readable rules, on-device matching, anonymous feedback, and mandatory official verification.",
      },
      { property: "og:title", content: "How Adhikar works" },
      {
        property: "og:description",
        content:
          "Readable eligibility rules, no accounts, no identity numbers stored, and every result links back to the official portal.",
      },
      { property: "og:type", content: "article" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: AboutPage,
});

const SECTIONS = [
  {
    title: "It is a discovery aid, not a decision",
    body: "Adhikar narrows thousands of possibilities down to a handful worth reading about. It cannot approve, reject, or register you for anything. Only the responsible department, bank, hospital, or local office can decide eligibility.",
  },
  {
    title: "Every result shows its reasoning",
    body: "Each scheme is checked against readable rules — age range, gender conditions, an income ceiling, urban or rural residence, and situation flags such as being a student, a farmer, or a street vendor. The result tells you which checks passed, which information is still missing, and which condition did not match.",
  },
  {
    title: "Your answers stay on your device",
    body: "The rule engine runs in your browser. Your age, income, gender, and category are never uploaded. Only an anonymous, redacted description of your need plus the scheme names are sent when you ask for a plain-language explanation.",
  },
  {
    title: "Identity numbers are removed automatically",
    body: "If you type an Aadhaar-like number, a phone number, an email address, or a PAN-like code, it is stripped out before anything leaves your device. Please never enter bank or card details anywhere in this app.",
  },
  {
    title: "Language and voice",
    body: "The interface is available in 13 Indian languages. You can speak your need instead of typing it, and you can listen to the explanation read aloud. Language never changes which schemes match — only how they are described.",
  },
  {
    title: "Feedback changes order, never eligibility",
    body: "The helpful and not useful buttons store one anonymous count per scheme. They gently adjust the presentation order so that entries people find useful surface sooner. They never change a pre-screen outcome.",
  },
  {
    title: "Always verify officially",
    body: "Scheme rules change often and this catalog is a small sample kept for demonstration. Confirm everything on myScheme (myscheme.gov.in) or with the department named on the official page before you spend time or money on an application.",
  },
];

function AboutPage() {
  return (
    <AdhikarLayout>
      <PageHeader
        eyebrow="How this works"
        title="Honest about what we can and cannot tell you"
        description="Adhikar is an independent prototype for finding Indian government schemes. It is not affiliated with or endorsed by the Government of India."
      />

      <div className="max-w-3xl">
        {SECTIONS.map((section) => (
          <section key={section.title} className="border-t border-border py-8">
            <h2 className="text-xl font-semibold">{section.title}</h2>
            <p className="mt-3 leading-relaxed text-muted-foreground">{section.body}</p>
          </section>
        ))}
      </div>
    </AdhikarLayout>
  );
}
