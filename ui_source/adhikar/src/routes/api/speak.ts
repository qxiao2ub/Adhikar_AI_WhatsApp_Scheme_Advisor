import { createFileRoute } from "@tanstack/react-router";
import { z } from "zod";

const bodySchema = z.object({
  text: z.string().trim().min(1).max(4000),
});

export const Route = createFileRoute("/api/speak")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const key = process.env.LOVABLE_API_KEY;
        if (!key) {
          return Response.json({ error: "Audio playback is not configured." }, { status: 500 });
        }

        let parsed: { text: string };
        try {
          parsed = bodySchema.parse(await request.json());
        } catch {
          return Response.json({ error: "Invalid request." }, { status: 400 });
        }

        // Strip markdown so the narration does not read symbols aloud.
        const spoken = parsed.text
          .replace(/[#*_`>|]/g, " ")
          .replace(/\[(.*?)\]\(.*?\)/g, "$1")
          .replace(/\s+/g, " ")
          .trim()
          .slice(0, 3500);

        const response = await fetch("https://ai.gateway.lovable.dev/v1/audio/speech", {
          method: "POST",
          headers: {
            Authorization: `Bearer ${key}`,
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            model: "openai/gpt-4o-mini-tts",
            input: spoken,
            voice: "alloy",
            response_format: "mp3",
            instructions:
              "Speak slowly, warmly and clearly, as if helping someone who is new to government paperwork.",
          }),
        });

        if (!response.ok) {
          const body = await response.text().catch(() => "");
          console.error(`Speech synthesis failed [${response.status}]: ${body}`);
          const message =
            response.status === 429
              ? "Too many requests. Please try again shortly."
              : response.status === 402
                ? "AI credits are exhausted."
                : "Audio could not be prepared.";
          return Response.json({ error: message }, { status: response.status });
        }

        return new Response(response.body, {
          headers: { "Content-Type": "audio/mpeg", "Cache-Control": "no-store" },
        });
      },
    },
  },
});
