import { z } from "zod";

export const overpassQuerySchema = z.object({
  lat: z.number().min(-90).max(90),
  lon: z.number().min(-180).max(180),
  radiusMeters: z.number().int().min(500).max(20000).default(5000),
});

export type NearbyPlace = {
  id: string;
  name: string;
  kind: string;
  lat: number;
  lon: number;
  distanceKm: number;
  address: string;
};

const KIND_LABELS: Record<string, string> = {
  hospital: "Hospital",
  clinic: "Clinic",
  doctors: "Health centre",
  pharmacy: "Pharmacy",
  bank: "Bank",
  post_office: "Post office",
  townhall: "Government office",
  community_centre: "Community centre",
  social_facility: "Social welfare facility",
  library: "Public library",
  school: "School",
  college: "College",
  police: "Police station",
};

function haversineKm(
  lat1: number,
  lon1: number,
  lat2: number,
  lon2: number,
): number {
  const toRad = (d: number) => (d * Math.PI) / 180;
  const R = 6371;
  const dLat = toRad(lat2 - lat1);
  const dLon = toRad(lon2 - lon1);
  const a =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRad(lat1)) * Math.cos(toRad(lat2)) * Math.sin(dLon / 2) ** 2;
  return 2 * R * Math.asin(Math.sqrt(a));
}

type OverpassElement = {
  type: string;
  id: number;
  lat?: number;
  lon?: number;
  center?: { lat: number; lon: number };
  tags?: Record<string, string>;
};

/** Look up nearby public services in OpenStreetMap via the Overpass API. */
export async function fetchNearbyServices(
  lat: number,
  lon: number,
  radiusMeters: number,
): Promise<NearbyPlace[]> {
  const amenities = Object.keys(KIND_LABELS).join("|");
  const query = `[out:json][timeout:25];
(
  node["amenity"~"^(${amenities})$"](around:${radiusMeters},${lat},${lon});
  way["amenity"~"^(${amenities})$"](around:${radiusMeters},${lat},${lon});
);
out center 80;`;

  const endpoints = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
  ];

  let response: Response | null = null;
  let lastError = "";
  for (const endpoint of endpoints) {
    const attempt = await fetch(endpoint, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        // Overpass rejects requests without an identifying user agent (406).
        "User-Agent": "Adhikar/1.0 (educational prototype)",
        Accept: "application/json",
      },
      body: new URLSearchParams({ data: query }).toString(),
    }).catch(() => null);

    if (attempt?.ok) {
      response = attempt;
      break;
    }
    lastError = attempt
      ? `${attempt.status}: ${(await attempt.text().catch(() => "")).slice(0, 160)}`
      : "network error";
  }

  if (!response) {
    console.error(`Overpass lookup failed: ${lastError}`);
    throw new Error("The map service is busy right now. Please try again in a moment.");
  }

  const payload = (await response.json()) as { elements?: OverpassElement[] };
  const elements = payload.elements ?? [];

  const places: NearbyPlace[] = [];
  for (const element of elements) {
    const plat = element.lat ?? element.center?.lat;
    const plon = element.lon ?? element.center?.lon;
    const tags = element.tags ?? {};
    if (plat === undefined || plon === undefined) continue;
    const amenity = tags.amenity ?? "";
    const name = tags["name:en"] || tags.name;
    if (!name) continue;
    const addressParts = [
      tags["addr:housenumber"],
      tags["addr:street"],
      tags["addr:suburb"],
      tags["addr:city"],
      tags["addr:postcode"],
    ].filter(Boolean);
    places.push({
      id: `${element.type}/${element.id}`,
      name,
      kind: KIND_LABELS[amenity] ?? amenity,
      lat: plat,
      lon: plon,
      distanceKm: haversineKm(lat, lon, plat, plon),
      address: addressParts.join(", "),
    });
  }

  places.sort((a, b) => a.distanceKm - b.distanceKm);
  return places.slice(0, 40);
}

export type GeocodeResult = {
  label: string;
  lat: number;
  lon: number;
};

/** Resolve a city / district / PIN code to coordinates using OpenStreetMap. */
export async function geocodePlace(queryText: string): Promise<GeocodeResult | null> {
  const url = new URL("https://nominatim.openstreetmap.org/search");
  url.searchParams.set("q", `${queryText}, India`);
  url.searchParams.set("format", "json");
  url.searchParams.set("limit", "1");
  url.searchParams.set("countrycodes", "in");

  const response = await fetch(url.toString(), {
    headers: {
      "User-Agent": "Adhikar/1.0 (educational prototype)",
      Accept: "application/json",
    },
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    throw new Error(
      `Location lookup failed (${response.status}): ${body.slice(0, 200)}`,
    );
  }

  const results = (await response.json()) as Array<{
    display_name: string;
    lat: string;
    lon: string;
  }>;
  if (!results.length) return null;
  return {
    label: results[0].display_name,
    lat: Number(results[0].lat),
    lon: Number(results[0].lon),
  };
}
