import { createClient } from "@supabase/supabase-js";
import type { Database } from "@/integrations/supabase/types";

/** Publishable-key Supabase client for public, read-only catalog access. */
export function createPublicSupabaseClient() {
  const url = process.env.SUPABASE_URL!;
  const key = process.env.SUPABASE_PUBLISHABLE_KEY!;
  return createClient<Database>(url, key, {
    auth: { persistSession: false, autoRefreshToken: false },
    global: {
      fetch: (input, init) => {
        const headers = new Headers(init?.headers);
        if (key.startsWith("sb_") && headers.get("Authorization") === `Bearer ${key}`) {
          headers.delete("Authorization");
        }
        headers.set("apikey", key);
        return fetch(input, { ...init, headers });
      },
    },
  });
}

export const AI_GATEWAY_URL = "https://ai.gateway.lovable.dev/v1";
export const SUMMARY_MODEL = "google/gemini-3.6-flash";

export type SummaryInput = {
  language: string;
  needText: string;
  results: Array<{
    name: string;
    status: string;
    reasons: string[];
    missing: string[];
    documents: string[];
  }>;
};

/**
 * Plain-language explanation of an already-computed pre-screen.
 * The model explains and translates. It never decides eligibility.
 */
export async function generateSummary(input: SummaryInput): Promise<string> {
  const key = process.env.LOVABLE_API_KEY;
  if (!key) throw new Error("AI service is not configured.");

  const catalog = input.results
    .map((r) => {
      const lines = [
        `Scheme: ${r.name}`,
        `Pre-screen outcome: ${r.status}`,
        r.reasons.length ? `Matched because: ${r.reasons.join(" ")}` : "",
        r.missing.length ? `Still needs: ${r.missing.join(", ")}` : "",
        r.documents.length ? `Commonly requested documents: ${r.documents.join(", ")}` : "",
      ].filter(Boolean);
      return lines.join("\n");
    })
    .join("\n\n");

  const systemPrompt = `You help people in India understand a government-scheme DISCOVERY pre-screen.

Absolute rules:
- You must NOT decide, grant, confirm, or deny eligibility. The pre-screen outcomes are already computed and given to you; restate them, never change them.
- Always tell the reader to verify everything on the official myScheme portal (https://www.myscheme.gov.in/) or with the responsible department, bank, hospital, or local authority.
- Never invent schemes, amounts, deadlines, or rules that are not in the data below.
- Never ask for or repeat identity numbers, phone numbers, or bank details.

Write your entire answer in ${input.language}. Use simple, respectful words that someone with limited formal education can follow. Use short markdown bullets. Keep it under 220 words.`;

  const userPrompt = `The person described their need as: "${input.needText || "(not described)"}"

Pre-screen results:

${catalog}

Explain in ${input.language}: what these results mean, which ones look most worth checking first, what documents to gather, and that an official check is still required.`;

  const response = await fetch(`${AI_GATEWAY_URL}/chat/completions`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      model: SUMMARY_MODEL,
      messages: [
        { role: "system", content: systemPrompt },
        { role: "user", content: userPrompt },
      ],
    }),
  });

  if (!response.ok) {
    const body = await response.text().catch(() => "");
    if (response.status === 429) {
      throw new Error("Too many requests right now. Please try again in a moment.");
    }
    if (response.status === 402) {
      throw new Error("AI credits are exhausted. Please add credits to continue.");
    }
    throw new Error(`AI summary failed (${response.status}): ${body.slice(0, 300)}`);
  }

  const payload = (await response.json()) as {
    choices?: Array<{ message?: { content?: string } }>;
  };
  return payload.choices?.[0]?.message?.content ?? "";
}
