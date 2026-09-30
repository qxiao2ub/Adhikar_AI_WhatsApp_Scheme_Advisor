import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { queryOptions, useSuspenseQuery } from "@tanstack/react-query";
import { Loader2 } from "lucide-react";
import { AdhikarLayout } from "@/components/adhikar-layout";
import { ProfileForm } from "@/components/profile-form";
import { ResultsList } from "@/components/results-list";
import { Button } from "@/components/ui/button";
import { useLanguage } from "@/components/language-provider";
import { getSchemeCatalog } from "@/lib/advisor.functions";
import { recommendSchemes } from "@/lib/scheme-engine";
import type { Recommendation, UserProfile } from "@/lib/scheme-types";

const catalogQuery = queryOptions({
  queryKey: ["scheme-catalog"],
  queryFn: () => getSchemeCatalog(),
  staleTime: 5 * 60 * 1000,
});

export const Route = createFileRoute("/advisor")({
  head: () => ({
    meta: [
      { title: "Find schemes — Adhikar" },
      {
        name: "description",
        content:
          "Answer a few optional questions and see which Indian government schemes are worth checking, with the reason for every result.",
      },
      { property: "og:title", content: "Find schemes — Adhikar" },
      {
        property: "og:description",
        content:
          "A transparent, rule-based pre-screen of Indian government schemes with plain-language explanations.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  loader: ({ context }) => context.queryClient.ensureQueryData(catalogQuery),
  pendingComponent: () => (
    <AdhikarLayout>
      <div className="flex justify-center py-20">
        <Loader2 className="size-8 animate-spin text-muted-foreground" aria-hidden="true" />
      </div>
    </AdhikarLayout>
  ),
  errorComponent: () => (
    <AdhikarLayout>
      <p className="py-20 text-center text-muted-foreground">
        The scheme catalog could not be loaded. Please try again.
      </p>
    </AdhikarLayout>
  ),
  component: AdvisorPage,
});

function AdvisorPage() {
  const { t } = useLanguage();
  const { data } = useSuspenseQuery(catalogQuery);
  const [profile, setProfile] = useState<UserProfile | null>(null);

  const results = useMemo<Recommendation[]>(() => {
    if (!profile) return [];
    // The rule engine runs here, in the browser: the profile never leaves the device.
    return recommendSchemes(profile, data.schemes, data.feedback, 6);
  }, [profile, data]);

  return (
    <AdhikarLayout>
      {profile ? (
        <div className="space-y-6">
          <Button variant="ghost" onClick={() => setProfile(null)}>
            ← {t("form.reset")}
          </Button>
          <ResultsList results={results} needText={profile.needText} />
        </div>
      ) : (
        <ProfileForm onSubmit={setProfile} />
      )}
    </AdhikarLayout>
  );
}
