import { createFileRoute } from "@tanstack/react-router";

const MAX_BYTES = 8 * 1024 * 1024;
const ALLOWED = ["audio/webm", "audio/mp4", "audio/mpeg", "audio/wav", "audio/x-wav"];

export const Route = createFileRoute("/api/transcribe")({
  server: {
    handlers: {
      POST: async ({ request }) => {
        const key = process.env.LOVABLE_API_KEY;
        if (!key) {
          return Response.json({ error: "Voice input is not configured." }, { status: 500 });
        }

        let form: FormData;
        try {
          form = await request.formData();
        } catch {
          return Response.json({ error: "Invalid upload." }, { status: 400 });
        }

        const audio = form.get("audio");
        if (!(audio instanceof File) || audio.size === 0) {
          return Response.json({ error: "No audio was received." }, { status: 400 });
        }
        if (audio.size > MAX_BYTES) {
          return Response.json({ error: "Recording is too long." }, { status: 413 });
        }
        const baseType = (audio.type || "audio/wav").split(";")[0];
        if (!ALLOWED.includes(baseType)) {
          return Response.json({ error: "Unsupported audio format." }, { status: 400 });
        }

        const language = String(form.get("language") ?? "").slice(0, 5);
        const upstream = new FormData();
        upstream.append("model", "openai/gpt-4o-mini-transcribe");
        upstream.append("file", audio, "recording.wav");
        if (language && language !== "en") upstream.append("language", language);

        const response = await fetch(
          "https://ai.gateway.lovable.dev/v1/audio/transcriptions",
          {
            method: "POST",
            headers: { Authorization: `Bearer ${key}` },
            body: upstream,
          },
        );

        if (!response.ok) {
          const body = await response.text().catch(() => "");
          console.error(`Transcription failed [${response.status}]: ${body}`);
          const message =
            response.status === 429
              ? "Too many requests. Please try again shortly."
              : response.status === 402
                ? "AI credits are exhausted."
                : "The recording could not be understood.";
          return Response.json({ error: message }, { status: response.status });
        }

        const payload = (await response.json()) as { text?: string };
        return Response.json({ text: payload.text ?? "" });
      },
    },
  },
});
