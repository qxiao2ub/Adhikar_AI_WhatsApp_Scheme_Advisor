import { createServerFn } from "@tanstack/react-start";
import { z } from "zod";
import {
  createPublicSupabaseClient,
  generateSummary,
} from "./advisor.server";
import { fetchNearbyServices, geocodePlace } from "./nearby.server";
import type { FeedbackCounts } from "./scheme-engine";
import type { SchemeRow } from "./scheme-types";

const feedbackSchema = z.object({
  schemeId: z.string().trim().min(1).max(80),
  helpful: z.boolean(),
});

const summarySchema = z.object({
  language: z.string().trim().min(2).max(40),
  needText: z.string().trim().max(1000),
  results: z
    .array(
      z.object({
        name: z.string().trim().max(200),
        status: z.string().trim().max(40),
        reasons: z.array(z.string().max(300)).max(12),
        missing: z.array(z.string().max(200)).max(12),
        documents: z.array(z.string().max(200)).max(12),
      }),
    )
    .min(1)
    .max(10),
});

const nearbySchema = z.object({
  lat: z.number().min(-90).max(90),
  lon: z.number().min(-180).max(180),
  radiusMeters: z.number().int().min(500).max(20000),
});

const geocodeSchema = z.object({
  query: z.string().trim().min(2).max(120),
});

/** Public catalog read: the scheme list plus aggregate feedback counts. */
export const getSchemeCatalog = createServerFn({ method: "GET" }).handler(
  async (): Promise<{ schemes: SchemeRow[]; feedback: FeedbackCounts }> => {
    const supabase = createPublicSupabaseClient();
    const [schemesRes, feedbackRes] = await Promise.all([
      supabase.from("schemes").select("*").order("name"),
      supabase
        .from("scheme_feedback")
        .select("scheme_id, helpful_count, not_helpful_count"),
    ]);

    if (schemesRes.error) throw new Error(schemesRes.error.message);

    const feedback: FeedbackCounts = {};
    for (const row of feedbackRes.data ?? []) {
      feedback[row.scheme_id] = {
        helpful_count: row.helpful_count,
        not_helpful_count: row.not_helpful_count,
      };
    }

    return { schemes: (schemesRes.data ?? []) as SchemeRow[], feedback };
  },
);

/** Aggregate-only helpful / not-helpful vote. No personal data is stored. */
export const submitSchemeFeedback = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) => feedbackSchema.parse(input))
  .handler(async ({ data }) => {
    const { supabaseAdmin } = await import("@/integrations/supabase/client.server");
    const { error } = await supabaseAdmin.rpc("record_scheme_feedback", {
      _scheme_id: data.schemeId,
      _helpful: data.helpful,
    });
    if (error) throw new Error(error.message);
    return { ok: true };
  });

/** Plain-language, translated explanation of results computed on the device. */
export const summarizeResults = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) => summarySchema.parse(input))
  .handler(async ({ data }) => {
    const summary = await generateSummary(data);
    return { summary };
  });

/** Nearby public services from open map data. */
export const findNearbyServices = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) => nearbySchema.parse(input))
  .handler(async ({ data }) => {
    const places = await fetchNearbyServices(data.lat, data.lon, data.radiusMeters);
    return { places };
  });

/** Resolve a city, district, or PIN code to coordinates. */
export const resolveLocation = createServerFn({ method: "POST" })
  .inputValidator((input: unknown) => geocodeSchema.parse(input))
  .handler(async ({ data }) => {
    const result = await geocodePlace(data.query);
    return { result };
  });
