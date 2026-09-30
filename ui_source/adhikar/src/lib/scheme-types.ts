// Shared, client-safe types for the Adhikar scheme discovery experience.

export type SchemeRow = {
  scheme_id: string;
  name: string;
  category: string;
  state_scope: string;
  min_age: number | null;
  max_age: number | null;
  allowed_genders: string | null;
  max_income: number | null;
  marital_statuses: string | null;
  residence: string | null;
  required_flags: string | null;
  occupation_keywords: string | null;
  need_keywords: string | null;
  documents: string | null;
  benefits: string | null;
  official_url: string | null;
  verification_note: string | null;
  special_rule: string | null;
};

export const NEED_FLAGS = [
  "student",
  "pregnant",
  "disability",
  "entrepreneur",
  "street_vendor",
  "farmer",
  "housing_need",
  "bank_account",
] as const;

export type NeedFlag = (typeof NEED_FLAGS)[number];

export const GENDERS = ["Female", "Male", "Other", "Prefer not to say"] as const;
export const MARITAL_STATUSES = [
  "Single",
  "Married",
  "Widowed",
  "Divorced",
  "Prefer not to say",
] as const;
export const RESIDENCES = ["Urban", "Rural", "Prefer not to say"] as const;
export const SOCIAL_CATEGORIES = [
  "General",
  "OBC",
  "SC",
  "ST",
  "Prefer not to say",
] as const;

export type UserProfile = {
  age: number | null;
  annualIncome: number | null;
  gender: string;
  maritalStatus: string;
  state: string;
  residence: string;
  socialCategory: string;
  needText: string;
} & Record<NeedFlag, boolean>;

export function emptyProfile(): UserProfile {
  return {
    age: null,
    annualIncome: null,
    gender: "Prefer not to say",
    maritalStatus: "Prefer not to say",
    state: "",
    residence: "Prefer not to say",
    socialCategory: "Prefer not to say",
    needText: "",
    student: false,
    pregnant: false,
    disability: false,
    entrepreneur: false,
    street_vendor: false,
    farmer: false,
    housing_need: false,
    bank_account: false,
  };
}

export type PrescreenStatus = "potential" | "review" | "unlikely";

export type Recommendation = {
  schemeId: string;
  name: string;
  category: string;
  status: PrescreenStatus;
  ruleScore: number;
  relevance: number;
  feedbackScore: number;
  finalScore: number;
  reasons: string[];
  missing: string[];
  failed: string[];
  documents: string[];
  benefits: string;
  officialUrl: string;
  verificationNote: string;
  helpfulCount: number;
  notHelpfulCount: number;
};

export const INDIAN_STATES = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  "Andaman and Nicobar Islands",
  "Chandigarh",
  "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi",
  "Jammu and Kashmir",
  "Ladakh",
  "Lakshadweep",
  "Puducherry",
];
