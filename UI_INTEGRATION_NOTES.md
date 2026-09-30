# Lovable UI Integration Notes

The attached `adhikar-source.zip` is preserved in full under `ui_source/adhikar/`. The deployed Streamlit app uses the Python recommendation core and ports the new UI's design system rather than requiring a second Node runtime.

## Integrated design elements

- Warm ivory background and paper surfaces from the source design tokens
- Deep navy foreground/navigation
- Restrained terracotta/saffron accent and green status accent
- DM-Serif-style editorial heading treatment using web-safe serif fallbacks
- Compact radii and low-shadow visual hierarchy
- Two-column home hero using the supplied `adhikar-hero.jpg`
- Source messaging: privacy, multilingual support, transparent pre-screening, and official verification
- Three-step discovery workflow adapted from the Lovable home route
- Streamlit tabs mapped to advisor, nearby help, AI transparency, deployment, and project-team functions
- Mobile-responsive layout

## Source materials kept in the repository

The `ui_source/adhikar/` folder contains the full supplied TanStack/React project, including components, routes, design styles, assets, configuration, and the Lovable/Supabase scaffolding that came with the design archive. These files are **not imported by the Streamlit runtime** and therefore do not add a Node or Supabase dependency to the deployed app. They are retained so the UI can be reproduced or extended later.

## Visitor count integration

The cumulative app-user count is intentionally implemented outside the supplied Supabase scaffolding. `visitor_counter.py` uses a flat JSON file. For persistence across Streamlit restarts, it can update the same JSON file through the GitHub Contents API. This meets the project's no-database requirement while avoiding identity tracking. See `VISITOR_COUNTER_SETUP.md`.
