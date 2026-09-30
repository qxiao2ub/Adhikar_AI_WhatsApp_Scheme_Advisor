-- Remove unused legacy asset-tracking tables (app is now Sahayak, anonymous, no code references these)
DROP TABLE IF EXISTS public.asset_assignments CASCADE;
DROP TABLE IF EXISTS public.assets CASCADE;
DROP TABLE IF EXISTS public.asset_categories CASCADE;
DROP TABLE IF EXISTS public.employees CASCADE;
DROP TABLE IF EXISTS public.user_roles CASCADE;
DROP FUNCTION IF EXISTS public.has_role(uuid, public.app_role) CASCADE;
DROP TYPE IF EXISTS public.asset_condition;

-- Keep the auth signup trigger function working, but make it a no-op now that roles are gone
CREATE OR REPLACE FUNCTION public.handle_new_user_role()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  RETURN NEW;
END;
$$;

-- Lock down SECURITY DEFINER functions: not callable by anon or signed-in API roles
REVOKE ALL ON FUNCTION public.handle_new_user_role() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.record_scheme_feedback(text, boolean) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.record_scheme_feedback(text, boolean) TO service_role;