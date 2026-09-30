import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { Loader2, ThumbsDown, ThumbsUp, Volume2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useLanguage } from "@/components/language-provider";
import { submitSchemeFeedback, summarizeResults } from "@/lib/advisor.functions";
import { redactSensitiveText } from "@/lib/scheme-engine";
import type { PrescreenStatus, Recommendation } from "@/lib/scheme-types";

const STATUS_STYLES: Record<PrescreenStatus, string> = {
  potential: "border-status-potential/40 bg-status-potential-soft text-status-potential",
  review: "border-status-review/40 bg-status-review-soft text-status-review",
  unlikely: "border-status-unlikely/40 bg-status-unlikely-soft text-status-unlikely",
};

type ResultsListProps = {
  results: Recommendation[];
  needText: string;
};

export function ResultsList({ results, needText }: ResultsListProps) {
  const { t, englishName } = useLanguage();
  const summarize = useServerFn(summarizeResults);
  const [summary, setSummary] = useState<string | null>(null);
  const [audioBusy, setAudioBusy] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);

  const summaryMutation = useMutation({
    mutationFn: () =>
      summarize({
        data: {
          language: englishName,
          needText: redactSensitiveText(needText).slice(0, 1000),
          results: results.slice(0, 6).map((result) => ({
            name: result.name,
            status: t(`results.status.${result.status}`),
            reasons: result.reasons.slice(0, 8),
            missing: result.missing.slice(0, 8),
            documents: result.documents.slice(0, 8),
          })),
        },
      }),
    onSuccess: (data) => setSummary(data.summary),
    onError: () => toast.error(t("summary.failed")),
  });

  const speak = async () => {
    if (audio) {
      audio.pause();
      setAudio(null);
      return;
    }
    if (!summary) return;
    setAudioBusy(true);
    try {
      const response = await fetch("/api/speak", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text: summary }),
      });
      if (!response.ok) throw new Error(t("summary.failed"));
      const element = new Audio(URL.createObjectURL(await response.blob()));
      element.onended = () => setAudio(null);
      await element.play();
      setAudio(element);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : t("error.generic"));
    } finally {
      setAudioBusy(false);
    }
  };

  if (results.length === 0) {
    return <p className="py-12 text-muted-foreground">{t("results.empty")}</p>;
  }

  return (
    <div className="max-w-3xl">
      <header className="border-b border-border pb-8">
        <h1 className="font-display text-[2.25rem] leading-[1.1]">{t("results.title")}</h1>
        <p className="mt-2 text-muted-foreground">{t("results.subtitle")}</p>
      </header>

      <section className="border-b border-border py-8">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 className="text-lg font-semibold">{t("summary.title")}</h2>
          {!summary ? (
            <Button
              size="sm"
              variant="outline"
              onClick={() => summaryMutation.mutate()}
              disabled={summaryMutation.isPending}
            >
              {summaryMutation.isPending && (
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              )}
              {summaryMutation.isPending ? t("summary.loading") : t("summary.generate")}
            </Button>
          ) : (
            <Button size="sm" variant="outline" onClick={speak} disabled={audioBusy}>
              {audioBusy ? (
                <Loader2 className="size-4 animate-spin" aria-hidden="true" />
              ) : (
                <Volume2 className="size-4" aria-hidden="true" />
              )}
              {audio ? t("summary.stop") : t("summary.listen")}
            </Button>
          )}
        </div>
        <div className="mt-4 leading-relaxed" aria-live="polite">
          {summary ? (
            <div className="space-y-2">
              {summary
                .split("\n")
                .map((line) => line.replace(/^[-*•]\s*/, "").replace(/[#*`]/g, "").trim())
                .filter(Boolean)
                .map((line, index) => (
                  <p key={index}>{line}</p>
                ))}
            </div>
          ) : (
            <p className="text-muted-foreground">{t("disclaimer.short")}</p>
          )}
        </div>
      </section>

      <div>
        {results.map((result) => (
          <SchemeResult key={result.schemeId} result={result} />
        ))}
      </div>
    </div>
  );
}

function SchemeResult({ result }: { result: Recommendation }) {
  const { t } = useLanguage();
  const sendFeedback = useServerFn(submitSchemeFeedback);
  const [voted, setVoted] = useState(false);

  const feedbackMutation = useMutation({
    mutationFn: (helpful: boolean) =>
      sendFeedback({ data: { schemeId: result.schemeId, helpful } }),
    onSuccess: () => {
      setVoted(true);
      toast.success(t("results.thanks"));
    },
    onError: () => toast.error(t("error.generic")),
  });

  return (
    <article className="border-b border-border py-10">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="font-display text-2xl">{result.name}</h2>
          <p className="mt-1 text-sm text-muted-foreground">{result.category}</p>
        </div>
        <span
          className={`rounded-md border px-2.5 py-1 text-sm font-medium ${STATUS_STYLES[result.status]}`}
        >
          {t(`results.status.${result.status}`)}
        </span>
      </div>

      <div className="mt-6 space-y-6">
        {result.benefits && (
          <Section title={t("results.benefits")}>
            <p className="leading-relaxed">{result.benefits}</p>
          </Section>
        )}

        {result.reasons.length > 0 && (
          <Section title={t("results.why")}>
            <List items={result.reasons} />
          </Section>
        )}

        {result.missing.length > 0 && (
          <Section title={t("results.missing")}>
            <List items={result.missing} />
          </Section>
        )}

        {result.failed.length > 0 && (
          <Section title={t("results.blocked")}>
            <List items={result.failed} />
          </Section>
        )}

        {result.documents.length > 0 && (
          <Section title={t("results.documents")}>
            <p className="leading-relaxed">{result.documents.join(" · ")}</p>
          </Section>
        )}

        {result.verificationNote && (
          <p className="text-sm text-muted-foreground">{result.verificationNote}</p>
        )}
      </div>

      <div className="mt-7 flex flex-wrap items-center gap-3">
        <Button asChild>
          <a href={result.officialUrl} target="_blank" rel="noreferrer noopener">
            {t("results.official")}
          </a>
        </Button>
        <div className="ms-auto flex items-center gap-1">
          <Button
            size="sm"
            variant="ghost"
            disabled={voted || feedbackMutation.isPending}
            onClick={() => feedbackMutation.mutate(true)}
          >
            <ThumbsUp className="size-4" aria-hidden="true" />
            {t("results.helpful")}
          </Button>
          <Button
            size="sm"
            variant="ghost"
            disabled={voted || feedbackMutation.isPending}
            onClick={() => feedbackMutation.mutate(false)}
          >
            <ThumbsDown className="size-4" aria-hidden="true" />
            {t("results.notHelpful")}
          </Button>
        </div>
      </div>
    </article>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="mb-1.5 text-sm font-semibold uppercase tracking-wide text-muted-foreground">
        {title}
      </h3>
      {children}
    </div>
  );
}

function List({ items }: { items: string[] }) {
  return (
    <ul className="list-disc space-y-1 ps-5 leading-relaxed">
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  );
}
