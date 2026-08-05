# Lovable UI Integration Notes

The supplied Lovable project was a React/TanStack visual prototype. This repository ports its visual system into Streamlit while preserving the Python recommendation engine and deployment model.

## Ported elements

- Cream handloom-paper background and cards
- Deep indigo sidebar/navigation
- Saffron and Ashoka-green accents
- Tricolour divider rules
- Rounded responsive cards and pill controls
- Inclusive Indian-community hero artwork
- Multilingual, privacy-first, transparent-pre-screening messaging

## Why the React runtime is not bundled

Streamlit Community Cloud launches `streamlit_app.py`. Keeping the deployed interface in Streamlit avoids a second Node build/runtime and keeps the prototype directly deployable from one repository. The supplied Lovable assets and design language are integrated into the Streamlit UI.
