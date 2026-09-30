import { useCallback, useRef, useState } from "react";
import { Loader2, Mic, Square } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { useLanguage } from "@/components/language-provider";

/** Encode captured mono PCM chunks into a complete 16-bit WAV file. */
function encodeWav(chunks: Float32Array[], sampleRate: number): Blob {
  let length = 0;
  for (const chunk of chunks) length += chunk.length;
  const buffer = new ArrayBuffer(44 + length * 2);
  const view = new DataView(buffer);
  const writeString = (offset: number, value: string) => {
    for (let i = 0; i < value.length; i++) view.setUint8(offset + i, value.charCodeAt(i));
  };
  writeString(0, "RIFF");
  view.setUint32(4, 36 + length * 2, true);
  writeString(8, "WAVE");
  writeString(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeString(36, "data");
  view.setUint32(40, length * 2, true);

  let offset = 44;
  for (const chunk of chunks) {
    for (let i = 0; i < chunk.length; i++) {
      const sample = Math.max(-1, Math.min(1, chunk[i]));
      view.setInt16(offset, sample < 0 ? sample * 0x8000 : sample * 0x7fff, true);
      offset += 2;
    }
  }
  return new Blob([buffer], { type: "audio/wav" });
}

type VoiceInputProps = {
  onTranscript: (text: string) => void;
};

export function VoiceInput({ onTranscript }: VoiceInputProps) {
  const { t, language } = useLanguage();
  const [state, setState] = useState<"idle" | "recording" | "working">("idle");
  const stopRef = useRef<(() => Promise<void>) | null>(null);

  const start = useCallback(async () => {
    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      toast.error(t("voice.failed"));
      return;
    }

    const ctx = new AudioContext();
    const source = ctx.createMediaStreamSource(stream);
    const processor = ctx.createScriptProcessor(4096, 1, 1);
    const chunks: Float32Array[] = [];
    processor.onaudioprocess = (event) => {
      chunks.push(new Float32Array(event.inputBuffer.getChannelData(0)));
    };
    source.connect(processor);
    processor.connect(ctx.destination);
    setState("recording");

    stopRef.current = async () => {
      stream.getTracks().forEach((track) => track.stop());
      processor.disconnect();
      source.disconnect();
      const blob = encodeWav(chunks, ctx.sampleRate);
      await ctx.close();

      if (blob.size < 4096) {
        setState("idle");
        toast.error(t("voice.failed"));
        return;
      }

      setState("working");
      try {
        const form = new FormData();
        form.append("audio", blob, "recording.wav");
        form.append("language", language);
        const response = await fetch("/api/transcribe", { method: "POST", body: form });
        const payload = (await response.json()) as { text?: string; error?: string };
        if (!response.ok || !payload.text?.trim()) {
          throw new Error(payload.error ?? t("voice.failed"));
        }
        onTranscript(payload.text.trim());
      } catch (error) {
        toast.error(error instanceof Error ? error.message : t("voice.failed"));
      } finally {
        setState("idle");
      }
    };
  }, [language, onTranscript, t]);

  if (state === "working") {
    return (
      <Button type="button" variant="secondary" disabled className="gap-2">
        <Loader2 className="size-4 animate-spin" aria-hidden="true" />
        {t("voice.transcribing")}
      </Button>
    );
  }

  if (state === "recording") {
    return (
      <Button
        type="button"
        variant="destructive"
        className="gap-2"
        onClick={() => stopRef.current?.()}
      >
        <Square className="size-4" aria-hidden="true" />
        {t("voice.stop")} · {t("voice.listening")}
      </Button>
    );
  }

  return (
    <Button type="button" variant="secondary" className="gap-2" onClick={start}>
      <Mic className="size-4" aria-hidden="true" />
      {t("voice.record")}
    </Button>
  );
}
