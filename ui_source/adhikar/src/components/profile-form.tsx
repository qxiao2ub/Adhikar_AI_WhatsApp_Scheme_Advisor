import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { useLanguage } from "@/components/language-provider";
import { VoiceInput } from "@/components/voice-input";
import type { TranslationKey } from "@/lib/i18n";
import {
  GENDERS,
  INDIAN_STATES,
  MARITAL_STATUSES,
  NEED_FLAGS,
  RESIDENCES,
  SOCIAL_CATEGORIES,
  emptyProfile,
  type UserProfile,
} from "@/lib/scheme-types";

type ProfileFormProps = {
  onSubmit: (profile: UserProfile) => void;
};

export function ProfileForm({ onSubmit }: ProfileFormProps) {
  const { t } = useLanguage();
  const [profile, setProfile] = useState<UserProfile>(emptyProfile);

  const update = <K extends keyof UserProfile>(key: K, value: UserProfile[K]) =>
    setProfile((current) => ({ ...current, [key]: value }));

  return (
    <div className="max-w-3xl">
      <header className="mb-10">
        <h1 className="font-display text-[2.25rem] leading-[1.1] sm:text-[2.75rem]">
          {t("form.title")}
        </h1>
        <p className="mt-3 text-lg leading-relaxed text-muted-foreground">{t("form.subtitle")}</p>
      </header>

      <form
        className="space-y-12"
        onSubmit={(event) => {
          event.preventDefault();
          onSubmit(profile);
        }}
      >
        <fieldset className="border-t border-border pt-8">
          <legend className="sr-only">{t("form.title")}</legend>
          <div className="grid gap-6 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="age">
                {t("form.age")}{" "}
                <span className="font-normal text-muted-foreground">({t("common.optional")})</span>
              </Label>
              <Input
                id="age"
                type="number"
                min={0}
                max={120}
                inputMode="numeric"
                value={profile.age ?? ""}
                onChange={(event) =>
                  update("age", event.target.value === "" ? null : Number(event.target.value))
                }
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="income">
                {t("form.income")}{" "}
                <span className="font-normal text-muted-foreground">({t("common.optional")})</span>
              </Label>
              <Input
                id="income"
                type="number"
                min={0}
                max={100000000}
                inputMode="numeric"
                value={profile.annualIncome ?? ""}
                onChange={(event) =>
                  update(
                    "annualIncome",
                    event.target.value === "" ? null : Number(event.target.value),
                  )
                }
              />
            </div>

            <SelectField
              id="gender"
              label={t("form.gender")}
              value={profile.gender}
              options={[...GENDERS]}
              onChange={(value) => update("gender", value)}
            />
            <SelectField
              id="marital"
              label={t("form.marital")}
              value={profile.maritalStatus}
              options={[...MARITAL_STATUSES]}
              onChange={(value) => update("maritalStatus", value)}
            />
            <SelectField
              id="residence"
              label={t("form.residence")}
              value={profile.residence}
              options={[...RESIDENCES]}
              onChange={(value) => update("residence", value)}
            />
            <SelectField
              id="category"
              label={t("form.category")}
              value={profile.socialCategory}
              options={[...SOCIAL_CATEGORIES]}
              onChange={(value) => update("socialCategory", value)}
            />

            <div className="space-y-2 sm:col-span-2">
              <Label htmlFor="state">
                {t("form.state")}{" "}
                <span className="font-normal text-muted-foreground">({t("common.optional")})</span>
              </Label>
              <Select
                value={profile.state || "__none"}
                onValueChange={(value) => update("state", value === "__none" ? "" : value)}
              >
                <SelectTrigger id="state">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="__none">{t("form.notSaid")}</SelectItem>
                  {INDIAN_STATES.map((state) => (
                    <SelectItem key={state} value={state}>
                      {state}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </fieldset>

        <fieldset className="border-t border-border pt-8">
          <legend className="mb-4 text-lg font-semibold">{t("form.needs")}</legend>
          <div className="grid gap-3 sm:grid-cols-2">
            {NEED_FLAGS.map((flag) => (
              <label
                key={flag}
                className={`flex min-h-11 cursor-pointer items-center gap-3 rounded-md border px-4 py-3 transition-colors ${
                  profile[flag]
                    ? "border-primary bg-secondary font-medium"
                    : "border-border hover:border-input"
                }`}
              >
                <Checkbox
                  checked={profile[flag]}
                  onCheckedChange={(checked) => update(flag, checked === true)}
                />
                <span className="text-sm">{t(`flag.${flag}` as TranslationKey)}</span>
              </label>
            ))}
          </div>
        </fieldset>

        <div className="space-y-3 border-t border-border pt-8">
          <Label htmlFor="needText" className="text-base">
            {t("form.needText")}
          </Label>
          <Textarea
            id="needText"
            rows={4}
            maxLength={1000}
            placeholder={t("form.needPlaceholder")}
            value={profile.needText}
            onChange={(event) => update("needText", event.target.value)}
          />
          <VoiceInput
            onTranscript={(text) =>
              setProfile((current) => ({
                ...current,
                needText: current.needText ? `${current.needText} ${text}` : text,
              }))
            }
          />
        </div>

        <div className="flex flex-wrap gap-3">
          <Button type="submit" size="lg">
            {t("form.submit")}
          </Button>
          <Button
            type="button"
            size="lg"
            variant="ghost"
            onClick={() => setProfile(emptyProfile())}
          >
            {t("form.reset")}
          </Button>
        </div>
      </form>
    </div>
  );
}

function SelectField({
  id,
  label,
  value,
  options,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <div className="space-y-2">
      <Label htmlFor={id}>{label}</Label>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger id={id}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {options.map((option) => (
            <SelectItem key={option} value={option}>
              {option}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
