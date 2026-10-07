# Lovable UI Integration Notes

The attached `adhikar-source.zip` is preserved under `ui_source/adhikar/`. The deployed Streamlit app uses the Python recommendation/backend core while porting the supplied Lovable design language rather than requiring a second Node runtime.

## Integrated design elements

- Warm ivory background and paper surfaces
- Deep navy navigation/foreground
- Terracotta/saffron accent and green status accent
- Editorial serif heading treatment
- Compact radii and restrained shadows
- Two-column hero using the supplied `adhikar-hero.jpg`
- Responsive Streamlit forms/cards/tabs
- Privacy and official-verification messaging
- Personalized scheme-discovery workflow
- Impact, privacy, human-help and admin sections that extend the original visual system

## Source materials preserved

`ui_source/adhikar/` contains the supplied TanStack/React project, components, routes, assets, configuration and Lovable/Supabase scaffolding. Those files are retained as design/development source material and are **not required by the Streamlit runtime**.

## Visitor counter vs beneficiary backend

The cumulative app-user counter remains intentionally separate from the new beneficiary-impact database:

- `visitor_counter.py` stores only a global session count and can optionally use GitHub-backed JSON persistence.
- `backend.py` stores only opt-in, privacy-minimized beneficiary/journey data and should use managed PostgreSQL for durable production deployment.

Do not merge beneficiary records into the GitHub visitor-count JSON file.
