// Transparent eligibility pre-screen + ranking.
//
// Ported from core_engine.py of the Adhikar scheme discovery prototype.
// This is a DISCOVERY aid: it never produces an official eligibility decision.
// Every rule below is readable, and every result carries its reasons.

import type {
  PrescreenStatus,
  Recommendation,
  SchemeRow,
  UserProfile,
} from "./scheme-types";

const NOT_SAID = "Prefer not to say";

/** Remove common Indian identifiers before text is stored or sent anywhere. */
export function redactSensitiveText(input: string): string {
  let text = input ?? "";
  text = text.replace(/\b\d{12}\b/g, "[REDACTED_ID_NUMBER]");
  text = text.replace(/\b(?:\+91[-\s]?)?[6-9]\d{9}\b/g, "[REDACTED_PHONE]");
  text = text.replace(
    /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g,
    "[REDACTED_EMAIL]",
  );
  text = text.replace(/\b[A-Z]{5}\d{4}[A-Z]\b/g, "[REDACTED_PAN_LIKE]");
  return text;
}

function isBlank(value: unknown): boolean {
  return value === null || value === undefined || String(value).trim() === "";
}

function splitList(value: string | null | undefined): string[] {
  if (isBlank(value)) return [];
  return String(value)
    .split(/[|,]/)
    .map((part) => part.trim())
    .filter(Boolean);
}

function tokenize(value: string): string[] {
  return (value ?? "")
    .toLowerCase()
    .split(/[^a-z0-9\u0900-\u0DFF]+/i)
    .filter((token) => token.length > 2);
}

type RuleAssessment = {
  ruleScore: number;
  status: PrescreenStatus;
  reasons: string[];
  missing: string[];
  failed: string[];
  checks: number;
  passed: number;
};

export function assessScheme(
  profile: UserProfile,
  scheme: SchemeRow,
): RuleAssessment {
  const reasons: string[] = [];
  const missing: string[] = [];
  const failed: string[] = [];
  let checks = 0;
  let passed = 0;

  const check = (
    condition: boolean | null,
    passReason: string,
    failReason: string,
    missingField = "",
  ) => {
    checks += 1;
    if (condition === null) {
      if (missingField) missing.push(missingField);
    } else if (condition) {
      passed += 1;
      reasons.push(passReason);
    } else {
      failed.push(failReason);
    }
  };

  // Age range
  if (!isBlank(scheme.min_age) || !isBlank(scheme.max_age)) {
    if (profile.age === null || Number.isNaN(profile.age)) {
      check(null, "", "", "age");
    } else {
      const minAge = isBlank(scheme.min_age) ? 0 : Number(scheme.min_age);
      const maxAge = isBlank(scheme.max_age) ? 200 : Number(scheme.max_age);
      check(
        profile.age >= minAge && profile.age <= maxAge,
        `Age ${profile.age} is within the catalog pre-screen range.`,
        `Age ${profile.age} is outside the catalog pre-screen range ${minAge}–${maxAge}.`,
      );
    }
  }

  // Gender
  const allowedGenders = splitList(scheme.allowed_genders);
  if (
    allowedGenders.length > 0 &&
    !allowedGenders.map((g) => g.toUpperCase()).includes("ALL")
  ) {
    if (profile.gender === NOT_SAID) {
      check(null, "", "", "gender");
    } else {
      check(
        allowedGenders.map((g) => g.toLowerCase()).includes(profile.gender.toLowerCase()),
        "Gender matches this catalog condition.",
        "Gender does not match this catalog condition.",
      );
    }
  }

  // Income ceiling
  if (!isBlank(scheme.max_income)) {
    if (profile.annualIncome === null || Number.isNaN(profile.annualIncome)) {
      check(null, "", "", "annual household income");
    } else {
      check(
        profile.annualIncome <= Number(scheme.max_income),
        "Income is within this broad discovery threshold.",
        "Income is above this broad discovery threshold; official rules may differ.",
      );
    }
  }

  // Residence (urban / rural)
  const residence = (scheme.residence ?? "").trim();
  if (residence && residence.toUpperCase() !== "ALL") {
    if (profile.residence === NOT_SAID || !profile.residence) {
      check(null, "", "", "urban or rural residence");
    } else {
      check(
        profile.residence.toLowerCase() === residence.toLowerCase(),
        `Residence matches this catalog condition (${residence}).`,
        `This catalog entry is pre-screened for ${residence} residence.`,
      );
    }
  }

  // Required situation flags
  for (const flag of splitList(scheme.required_flags)) {
    const value = (profile as unknown as Record<string, unknown>)[flag];
    const label = flag.replace(/_/g, " ");
    check(
      value === true,
      `Profile indicates ${label}.`,
      `This catalog entry expects ${label}.`,
    );
  }

  // Special rules carried over from the reference engine
  const special = (scheme.special_rule ?? "").trim();
  if (special === "standup") {
    if (profile.gender === NOT_SAID && profile.socialCategory === NOT_SAID) {
      check(null, "", "", "gender or eligible social category");
    } else {
      check(
        profile.gender === "Female" ||
          profile.socialCategory === "SC" ||
          profile.socialCategory === "ST",
        "Profile meets the broad women / SC / ST discovery condition.",
        "This catalog pre-screen expects a woman entrepreneur or an SC/ST entrepreneur.",
      );
    }
  } else if (special === "apy") {
    if (!profile.bank_account) {
      failed.push(
        "This catalog pre-screen expects a savings bank or post-office savings account.",
      );
    } else {
      reasons.push(
        "Profile indicates an eligible type of savings account may be available.",
      );
    }
  } else if (special === "jssk") {
    // Government-facility admission is intentionally left for official confirmation.
    missing.push("confirmation from a government health institution");
  }

  let ruleScore: number;
  let status: PrescreenStatus;
  if (failed.length > 0) {
    ruleScore = 0.05;
    status = "unlikely";
  } else if (missing.length > 0) {
    const completion = passed / Math.max(checks, 1);
    ruleScore = 0.55 + 0.25 * completion;
    status = "review";
  } else {
    ruleScore = checks ? 0.92 : 0.72;
    status = "potential";
  }

  return {
    ruleScore: Math.min(Math.max(ruleScore, 0), 1),
    status,
    reasons,
    missing: Array.from(new Set(missing)).sort(),
    failed,
    checks,
    passed,
  };
}

function buildQuery(profile: UserProfile): string {
  const parts = [
    redactSensitiveText(profile.needText ?? ""),
    profile.student ? "student education scholarship" : "",
    profile.pregnant ? "pregnancy maternal healthcare" : "",
    profile.disability ? "disability support" : "",
    profile.entrepreneur ? "entrepreneur business loan" : "",
    profile.street_vendor ? "street vendor livelihood" : "",
    profile.farmer ? "farmer agriculture" : "",
    profile.housing_need ? "housing shelter" : "",
  ];
  const query = parts.filter(Boolean).join(" ").trim();
  return query || "government benefit support";
}

/** Cosine-style keyword overlap, replacing the reference TF-IDF retriever. */
function relevanceScore(queryTokens: string[], scheme: SchemeRow): number {
  const schemeTokens = tokenize(
    [scheme.name, scheme.category, scheme.need_keywords, scheme.occupation_keywords]
      .filter(Boolean)
      .join(" "),
  );
  if (queryTokens.length === 0 || schemeTokens.length === 0) return 0;
  const schemeSet = new Set(schemeTokens);
  const querySet = new Set(queryTokens);
  let matches = 0;
  for (const token of querySet) if (schemeSet.has(token)) matches += 1;
  return matches / Math.sqrt(querySet.size * schemeSet.size);
}

export type FeedbackCounts = Record<
  string,
  { helpful_count: number; not_helpful_count: number }
>;

/** Aggregate helpful/not-helpful signal — presentation order only. */
export function feedbackScore(
  schemeId: string,
  feedback: FeedbackCounts,
): number {
  const row = feedback[schemeId];
  if (!row) return 0.5;
  const total = row.helpful_count + row.not_helpful_count;
  if (total === 0) return 0.5;
  // Laplace-smoothed mean reward, so a single vote cannot dominate.
  return (row.helpful_count + 1) / (total + 2);
}

export function recommendSchemes(
  profile: UserProfile,
  schemes: SchemeRow[],
  feedback: FeedbackCounts = {},
  topK = 6,
): Recommendation[] {
  const queryTokens = tokenize(buildQuery(profile));
  const stateScoped = schemes.filter((scheme) => {
    const scope = (scheme.state_scope ?? "ALL").trim();
    if (!scope || scope.toUpperCase() === "ALL") return true;
    if (!profile.state) return true;
    return scope.toLowerCase() === profile.state.toLowerCase();
  });

  const results: Recommendation[] = stateScoped.map((scheme) => {
    const rules = assessScheme(profile, scheme);
    const relevance = relevanceScore(queryTokens, scheme);
    const feedbackValue = feedbackScore(scheme.scheme_id, feedback);
    const counts = feedback[scheme.scheme_id];

    // Eligibility never depends on feedback; feedback only nudges order.
    const base = 0.6 * rules.ruleScore + 0.4 * Math.min(relevance * 2.5, 1);
    const finalScore = base * (0.9 + 0.2 * feedbackValue);

    return {
      schemeId: scheme.scheme_id,
      name: scheme.name,
      category: scheme.category,
      status: rules.status,
      ruleScore: rules.ruleScore,
      relevance,
      feedbackScore: feedbackValue,
      finalScore,
      reasons: rules.reasons,
      missing: rules.missing,
      failed: rules.failed,
      documents: splitList(scheme.documents),
      benefits: scheme.benefits ?? "",
      officialUrl: scheme.official_url || "https://www.myscheme.gov.in/",
      verificationNote: scheme.verification_note ?? "",
      helpfulCount: counts?.helpful_count ?? 0,
      notHelpfulCount: counts?.not_helpful_count ?? 0,
    };
  });

  const rank = { potential: 0, review: 1, unlikely: 2 } as const;
  results.sort((a, b) => {
    if (rank[a.status] !== rank[b.status]) return rank[a.status] - rank[b.status];
    return b.finalScore - a.finalScore;
  });

  const eligible = results.filter((r) => r.status !== "unlikely");
  const rest = results.filter((r) => r.status === "unlikely");
  return [...eligible, ...rest].slice(0, Math.max(topK, eligible.length ? topK : 3));
}
