import base64
import json

import streamlit as st
from openai import OpenAI

from constants import STIL_OPTIONEN, TECHNIK_OPTIONEN, GATTUNG_OPTIONEN


def bild_als_base64_data_url(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    mime_type = uploaded_file.type or "image/jpeg"

    return f"data:{mime_type};base64,{encoded}"


def ki_upload_analyse(uploaded_file, kuenstler, titel, jahr):
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key)

    data_url = bild_als_base64_data_url(uploaded_file)

    prompt = f"""
Du bist Kunsthistoriker und Museumsredakteur.

Analysiere das hochgeladene Kunstwerk.

Die folgenden Angaben gelten als korrekt:
Künstler: {kuenstler}
Titel: {titel}
Jahr: {jahr}

Aufgabe:
- Formuliere eine sachliche Beschreibung.
- Erzeuge sinnvolle Schlagworte.
- Schätze die Technik vorsichtig ein.
- Wähle passende Stile/Epochen ausschließlich aus dieser Liste:
{", ".join(STIL_OPTIONEN)}
- Wähle passende Techniken ausschließlich aus dieser Liste:
{", ".join(TECHNIK_OPTIONEN)}
- Wähle passende Gattungen/Motive ausschließlich aus dieser Liste:
{", ".join(GATTUNG_OPTIONEN)}
- Keine erfundenen Zusatzinformationen.
- Schlagworte sollen Künstler und Titel enthalten, sofern diese angegeben wurden.

Gib ausschließlich gültiges JSON zurück, ohne Markdown.

Schema:
{{
  "technik": "",
  "beschreibung": "",
  "schlagworte": "",
  "stile": "",
  "techniken": "",
  "gattungen": ""
}}

Mehrfachwerte kommasepariert ausgeben.
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                    {
                        "type": "input_image",
                        "image_url": data_url,
                    },
                ],
            }
        ],
    )

    text = response.output_text.strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        return {
            "technik": "",
            "beschreibung": text,
            "schlagworte": "",
            "stile": "",
            "techniken": "",
            "gattungen": "",
        }