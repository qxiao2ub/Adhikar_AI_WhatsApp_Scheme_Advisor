REVOKE EXECUTE ON FUNCTION public.record_scheme_feedback(TEXT, BOOLEAN) FROM anon, authenticated, public;
GRANT EXECUTE ON FUNCTION public.record_scheme_feedback(TEXT, BOOLEAN) TO service_role;