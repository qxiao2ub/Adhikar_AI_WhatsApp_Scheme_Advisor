CREATE TABLE public.schemes (
  scheme_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  state_scope TEXT NOT NULL DEFAULT 'ALL',
  min_age INTEGER,
  max_age INTEGER,
  allowed_genders TEXT,
  max_income NUMERIC,
  marital_statuses TEXT,
  residence TEXT,
  required_flags TEXT,
  occupation_keywords TEXT,
  need_keywords TEXT,
  documents TEXT,
  benefits TEXT,
  official_url TEXT,
  verification_note TEXT,
  special_rule TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT ON public.schemes TO anon;
GRANT SELECT ON public.schemes TO authenticated;
GRANT ALL ON public.schemes TO service_role;

ALTER TABLE public.schemes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Scheme catalog is publicly readable"
  ON public.schemes FOR SELECT TO anon, authenticated USING (true);

CREATE TABLE public.scheme_feedback (
  scheme_id TEXT PRIMARY KEY REFERENCES public.schemes(scheme_id) ON DELETE CASCADE,
  helpful_count INTEGER NOT NULL DEFAULT 0,
  not_helpful_count INTEGER NOT NULL DEFAULT 0,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

GRANT SELECT ON public.scheme_feedback TO anon;
GRANT SELECT ON public.scheme_feedback TO authenticated;
GRANT ALL ON public.scheme_feedback TO service_role;

ALTER TABLE public.scheme_feedback ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Aggregate feedback is publicly readable"
  ON public.scheme_feedback FOR SELECT TO anon, authenticated USING (true);

CREATE OR REPLACE FUNCTION public.record_scheme_feedback(_scheme_id TEXT, _helpful BOOLEAN)
RETURNS void
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM public.schemes WHERE scheme_id = _scheme_id) THEN
    RAISE EXCEPTION 'Unknown scheme';
  END IF;
  INSERT INTO public.scheme_feedback (scheme_id, helpful_count, not_helpful_count)
  VALUES (_scheme_id, CASE WHEN _helpful THEN 1 ELSE 0 END, CASE WHEN _helpful THEN 0 ELSE 1 END)
  ON CONFLICT (scheme_id) DO UPDATE SET
    helpful_count = public.scheme_feedback.helpful_count + CASE WHEN _helpful THEN 1 ELSE 0 END,
    not_helpful_count = public.scheme_feedback.not_helpful_count + CASE WHEN _helpful THEN 0 ELSE 1 END,
    updated_at = now();
END;
$$;

GRANT EXECUTE ON FUNCTION public.record_scheme_feedback(TEXT, BOOLEAN) TO anon, authenticated, service_role;

INSERT INTO public.schemes (scheme_id, name, category, state_scope, min_age, max_age, allowed_genders, max_income, marital_statuses, residence, required_flags, occupation_keywords, need_keywords, documents, benefits, official_url, verification_note, special_rule) VALUES
('atal_pension_yojana','Atal Pension Yojana','Pension','ALL',18,40,'ALL',NULL,'ALL','ALL','bank_account','worker informal sector pension retirement','pension retirement old age savings social security','Aadhaar or accepted identity proof|Active mobile number|Savings bank or post-office savings account|Other documents requested by the bank','Contributory pension support after age 60, subject to official rules and enrollment conditions.','https://www.myscheme.gov.in/','Illustrative pre-screen. Confirm tax-payer status, existing statutory social-security enrollment, contribution amount, and current official conditions.','apy'),
('janani_shishu_suraksha','Janani Shishu Suraksha Karyakram','Health','ALL',NULL,NULL,'Female',NULL,'ALL','ALL','pregnant','pregnant mother maternal newborn','pregnancy childbirth maternal health hospital newborn healthcare','Identity proof|Pregnancy or antenatal records|Hospital registration documents|Other documents requested by the government health institution','Maternal and newborn health support at government health institutions, subject to official conditions.','https://www.myscheme.gov.in/','Illustrative pre-screen. Availability and procedures must be confirmed with the relevant government health institution.','jssk'),
('stand_up_india','Stand-Up India','Business','ALL',18,NULL,'ALL',NULL,'ALL','ALL','entrepreneur','entrepreneur business startup greenfield enterprise','business loan enterprise startup women entrepreneur financing','Identity and address proof|Business plan|Bank documents|Category or gender-related supporting document where applicable|Other lender-required documents','Bank-loan facilitation for eligible greenfield enterprises, subject to lender and official program rules.','https://www.myscheme.gov.in/','Illustrative pre-screen. Official eligibility includes enterprise, ownership/control, greenfield-project, and banking conditions.','standup'),
('pm_svanidhi','PM Street Vendor’s AtmaNirbhar Nidhi (PM SVANidhi)','Livelihood','ALL',18,NULL,'ALL',NULL,'ALL','Urban','street_vendor','street vendor hawker livelihood micro business','working capital loan street vending livelihood business','Identity proof|Vendor certificate or identification letter, where applicable|Bank account details|Mobile number|Other documents requested by the implementing body','Working-capital support for eligible street vendors, subject to current official rules.','https://www.myscheme.gov.in/','Illustrative pre-screen. Vendor identification and local implementing-body rules require official verification.',NULL),
('pm_kisan','Pradhan Mantri Kisan Samman Nidhi (PM-KISAN)','Agriculture','ALL',18,NULL,'ALL',NULL,'ALL','Rural','farmer','farmer agriculture landholder cultivation','farm income agriculture crop financial support','Aadhaar|Land records as required|Bank account details|Mobile number|Other documents requested by the State or UT','Income support for eligible farmer families, subject to land records, exclusion criteria, and official verification.','https://www.myscheme.gov.in/','Illustrative pre-screen. Landholding and exclusion criteria are not fully modeled.',NULL),
('old_age_pension_search','Old-Age Pension Scheme Search','Pension','ALL',60,NULL,'ALL',250000,'ALL','ALL',NULL,'senior citizen elderly pension','old age pension senior citizen income support','Age proof|Identity proof|Address or domicile proof|Income or BPL proof where required|Bank account details','Routes the user to relevant Central or State/UT old-age pension schemes for official review.','https://www.myscheme.gov.in/','Discovery aid only. Age thresholds, income limits, and residency rules vary by scheme and State/UT.',NULL),
('scholarship_search','Student Scholarship Scheme Search','Education','ALL',6,35,'ALL',800000,'ALL','ALL','student','student school college university learner','scholarship tuition education study books hostel','Student identity or admission proof|Academic records|Income certificate where required|Bank account details|Category or disability certificate only when a selected scheme requires it','Finds potentially relevant Central and State/UT scholarship schemes for further official eligibility checks.','https://www.myscheme.gov.in/','Discovery aid only. Every scholarship has separate academic, income, institution, domicile, and category conditions.',NULL),
('disability_support_search','Disability Support Scheme Search','Social Welfare','ALL',NULL,NULL,'ALL',500000,'ALL','ALL','disability','person with disability divyang caregiver accessibility','disability pension assistive device scholarship rehabilitation support','Identity proof|Disability certificate or UDID where required|Address or domicile proof|Income certificate where required|Bank account details','Finds potentially relevant disability-support schemes and directs the user to official verification.','https://www.myscheme.gov.in/','Discovery aid only. Disability percentage, certification, income, age, and State/UT rules vary.',NULL),
('housing_support_search','Housing Assistance Scheme Search','Housing','ALL',18,NULL,'ALL',600000,'ALL','ALL','housing_need','household family housing homeless kutcha house','housing home construction rent shelter rural urban','Identity proof|Address or domicile proof|Income proof|Land or housing records where applicable|Bank account details','Finds potentially relevant rural or urban housing-assistance schemes for official review.','https://www.myscheme.gov.in/','Discovery aid only. Housing ownership, family composition, local lists, and income categories require official verification.',NULL),
('ayushman_health_search','Public Health Coverage Scheme Search','Health','ALL',NULL,NULL,'ALL',NULL,'ALL','ALL',NULL,'patient family healthcare hospital treatment insurance','healthcare hospital surgery treatment insurance medical benefit','Identity proof|Family or beneficiary identification requested by the scheme|Ration card or other household record where applicable|Other documents requested by the hospital or implementing authority','Finds potentially relevant public health-benefit and insurance schemes for official beneficiary verification.','https://www.myscheme.gov.in/','Discovery aid only. Many health schemes use beneficiary databases and conditions that cannot be inferred from income alone.',NULL),
('women_support_search','Women and Family Support Scheme Search','Women and Child','ALL',18,NULL,'Female',500000,'ALL','ALL',NULL,'woman mother widow family caregiver','women support widow maternity safety livelihood family benefit','Identity proof|Address or domicile proof|Income proof where required|Marital or family-status document only when a selected scheme requires it|Bank account details','Finds potentially relevant women- and family-support schemes for official review.','https://www.myscheme.gov.in/','Discovery aid only. Exact conditions vary by selected scheme and State/UT.',NULL),
('skill_training_search','Skill Development and Training Scheme Search','Skills','ALL',15,59,'ALL',NULL,'ALL','ALL',NULL,'job seeker youth worker trainee unemployed','skill training job employment certification apprenticeship','Identity proof|Age proof|Education records where required|Bank account details for stipend-linked programs|Other training-provider documents','Finds potentially relevant skill-development, apprenticeship, and training schemes.','https://www.myscheme.gov.in/','Discovery aid only. Course, age, education, location, and provider conditions vary.',NULL);