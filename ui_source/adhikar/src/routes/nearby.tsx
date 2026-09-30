import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { useServerFn } from "@tanstack/react-start";
import { Loader2, LocateFixed, Search } from "lucide-react";
import { toast } from "sonner";
import { AdhikarLayout } from "@/components/adhikar-layout";
import { PageHeader } from "@/components/page-header";
import { useLanguage } from "@/components/language-provider";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { findNearbyServices, resolveLocation } from "@/lib/advisor.functions";
import type { NearbyPlace } from "@/lib/nearby.server";

export const Route = createFileRoute("/nearby")({
  head: () => ({
    meta: [
      { title: "Nearby help — Adhikar" },
      {
        name: "description",
        content:
          "Find nearby hospitals, banks, post offices, and government offices in India using open map data.",
      },
      { property: "og:title", content: "Nearby help — Adhikar" },
      {
        property: "og:description",
        content:
          "Search by your location or a PIN code to find the offices where government schemes are actually applied for.",
      },
      { property: "og:type", content: "website" },
      { name: "twitter:card", content: "summary" },
    ],
  }),
  component: NearbyPage,
});

function NearbyPage() {
  const { t } = useLanguage();
  const nearby = useServerFn(findNearbyServices);
  const geocode = useServerFn(resolveLocation);
  const [query, setQuery] = useState("");
  const [radius, setRadius] = useState("5000");
  const [places, setPlaces] = useState<NearbyPlace[] | null>(null);
  const [label, setLabel] = useState("");

  const search = useMutation({
    mutationFn: async (coords: { lat: number; lon: number }) =>
      nearby({ data: { ...coords, radiusMeters: Number(radius) } }),
    onSuccess: (data) => setPlaces(data.places),
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : t("error.generic")),
  });

  const searchByText = useMutation({
    mutationFn: async () => {
      const { result } = await geocode({ data: { query } });
      if (!result) throw new Error(t("nearby.empty"));
      setLabel(result.label);
      return search.mutateAsync({ lat: result.lat, lon: result.lon });
    },
    onError: (error) =>
      toast.error(error instanceof Error ? error.message : t("error.generic")),
  });

  const useMyLocation = () => {
    if (!navigator.geolocation) {
      toast.error(t("nearby.locationDenied"));
      return;
    }
    navigator.geolocation.getCurrentPosition(
      (position) => {
        setLabel("");
        search.mutate({
          lat: position.coords.latitude,
          lon: position.coords.longitude,
        });
      },
      () => toast.error(t("nearby.locationDenied")),
    );
  };

  const busy = search.isPending || searchByText.isPending;

  return (
    <AdhikarLayout>
      <PageHeader eyebrow="Nearby" title={t("nearby.title")} description={t("nearby.subtitle")} />

      <section className="max-w-3xl border-t border-border pt-8">
        <Button onClick={useMyLocation} disabled={busy} variant="outline">
          <LocateFixed className="size-4" aria-hidden="true" />
          {t("nearby.useLocation")}
        </Button>

        <form
          className="mt-6 grid gap-4 sm:grid-cols-[1fr_auto_auto] sm:items-end"
          onSubmit={(event) => {
            event.preventDefault();
            if (query.trim().length >= 2) searchByText.mutate();
          }}
        >
          <div className="space-y-2">
            <Label htmlFor="place">{t("nearby.searchLabel")}</Label>
            <Input
              id="place"
              value={query}
              maxLength={120}
              placeholder={t("nearby.searchPlaceholder")}
              onChange={(event) => setQuery(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="radius">{t("nearby.radius")}</Label>
            <Select value={radius} onValueChange={setRadius}>
              <SelectTrigger id="radius" className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="2000">2 km</SelectItem>
                <SelectItem value="5000">5 km</SelectItem>
                <SelectItem value="10000">10 km</SelectItem>
                <SelectItem value="20000">20 km</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <Button type="submit" disabled={busy || query.trim().length < 2}>
            {busy ? (
              <Loader2 className="size-4 animate-spin" aria-hidden="true" />
            ) : (
              <Search className="size-4" aria-hidden="true" />
            )}
            {t("nearby.search")}
          </Button>
        </form>

        {label && <p className="mt-4 text-sm text-muted-foreground">{label}</p>}
      </section>

      <div aria-live="polite">
        {busy && <p className="py-12 text-muted-foreground">{t("nearby.loading")}</p>}

        {!busy && places && places.length === 0 && (
          <p className="py-12 text-muted-foreground">{t("nearby.empty")}</p>
        )}

        {!busy && places && places.length > 0 && (
          <ul className="mt-12 grid gap-x-10 sm:grid-cols-2">
            {places.map((place) => (
              <li key={place.id} className="border-t border-border py-6">
                <p className="text-sm uppercase tracking-wide text-muted-foreground">
                  {place.kind}
                </p>
                <h2 className="mt-1 text-lg font-semibold">{place.name}</h2>
                {place.address && (
                  <p className="mt-1 text-sm text-muted-foreground">{place.address}</p>
                )}
                <p className="mt-2 text-sm">
                  {place.distanceKm.toFixed(1)} km {t("nearby.away")}
                </p>
                <a
                  className="mt-3 inline-block text-sm font-medium text-primary underline underline-offset-4"
                  href={`https://www.openstreetmap.org/?mlat=${place.lat}&mlon=${place.lon}#map=17/${place.lat}/${place.lon}`}
                  target="_blank"
                  rel="noreferrer noopener"
                >
                  {t("nearby.directions")}
                </a>
              </li>
            ))}
          </ul>
        )}
      </div>
    </AdhikarLayout>
  );
}
