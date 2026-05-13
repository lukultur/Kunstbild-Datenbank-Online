import streamlit as st
import pandas as pd
import base64
import json
import uuid
import requests
from pathlib import Path
from io import BytesIO
from openai import OpenAI
from supabase import create_client

PASSWORT = "kunstarchiv2026"

st.set_page_config(page_title="Kunstbild-Datenbank", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_BUCKET = st.secrets["SUPABASE_BUCKET"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def login_pruefen():
    st.title("Kunstbild-Datenbank")
    st.subheader("Geschützter Zugang")

    eingabe = st.text_input(
        "Passwort eingeben",
        type="password"
    )

    if eingabe == PASSWORT:
        st.session_state["eingeloggt"] = True
        st.rerun()

    elif eingabe:
        st.error("Falsches Passwort.")


if "eingeloggt" not in st.session_state:
    st.session_state["eingeloggt"] = False

if "seite" not in st.session_state:
    st.session_state["seite"] = "Archiv durchsuchen"

if "ansicht" not in st.session_state:
    st.session_state["ansicht"] = "Galerieansicht"

if "ausgewaehlte_id" not in st.session_state:
    st.session_state["ausgewaehlte_id"] = None

if "ki_upload_analyse" not in st.session_state:
    st.session_state["ki_upload_analyse"] = {}

if not st.session_state["eingeloggt"]:
    login_pruefen()
    st.stop()


st.title("Kunstbild-Datenbank")
st.caption(
    "Recherche, Vorschau, Upload, Export, KI-Analyse und Verwaltung deiner Kunstbilder"
)


def daten_laden():

    response = (
        supabase.table("kunstbilder")
        .select("*")
        .order("titel")
        .execute()
    )

    df = pd.DataFrame(response.data)

    if df.empty:

        df = pd.DataFrame(
            columns=[
                "id",
                "dateiname",
                "kuenstler",
                "titel",
                "jahr",
                "technik",
                "masse",
                "standort",
                "rechte",
                "beschreibung",
                "schlagworte",
                "bildpfad",
            ]
        )

    return df.fillna("")


def excel_export_erzeugen(df):

    export_df = df.drop(
        columns=["id"],
        errors="ignore"
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl"
    ) as writer:

        export_df.to_excel(
            writer,
            index=False,
            sheet_name="Kunstbilder"
        )

    output.seek(0)

    return output


def datensatz_speichern(daten):

    supabase.table(
        "kunstbilder"
    ).insert(daten).execute()


def datensatz_aktualisieren(
    datensatz_id,
    daten
):

    url = (
        f"{SUPABASE_URL}/rest/v1/kunstbilder"
        f"?id=eq.{int(datensatz_id)}"
    )

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    response = requests.patch(
        url,
        headers=headers,
        json=daten,
        timeout=30,
    )

    if response.status_code not in (
        200,
        204,
    ):

        raise RuntimeError(
            f"Supabase-Update fehlgeschlagen: "
            f"{response.status_code} - "
            f"{response.text}"
        )


def datensatz_loeschen(
    datensatz_id,
    dateiname
):

    try:

        supabase.storage.from_(
            SUPABASE_BUCKET
        ).remove([str(dateiname)])

    except:
        pass

    supabase.table(
        "kunstbilder"
    ).delete().eq(
        "id",
        datensatz_id
    ).execute()


def kurzer_titel(
    text,
    max_laenge=18
):

    text = str(text)

    if len(text) > max_laenge:
        return text[:max_laenge] + "..."

    return text


def bild_als_base64_data_url(
    bild_url
):

    response = requests.get(
        bild_url,
        timeout=30
    )

    encoded = base64.b64encode(
        response.content
    ).decode("utf-8")

    return (
        f"data:image/jpeg;base64,"
        f"{encoded}"
    )


def uploaded_file_als_base64_data_url(
    uploaded_file
):

    file_bytes = (
        uploaded_file.getvalue()
    )

    encoded = base64.b64encode(
        file_bytes
    ).decode("utf-8")

    mime_type = (
        uploaded_file.type
        or
        "image/jpeg"
    )

    return (
        f"data:{mime_type};base64,"
        f"{encoded}"
    )


def ki_recherche_fuer_bild(
    uploaded_file
):

    api_key = st.secrets.get(
        "OPENAI_API_KEY",
        ""
    )

    client = OpenAI(
        api_key=api_key
    )

    data_url = (
        uploaded_file_als_base64_data_url(
            uploaded_file
        )
    )

    prompt = """
Du bist Kunsthistoriker, Museumsarchivar und Bildredakteur.

Analysiere das hochgeladene Kunstwerk.

WICHTIG:
- Erfinde niemals Künstlernamen.
- Erfinde niemals Bildtitel.
- Erfinde niemals Datierungen.
- Wenn du nicht absolut sicher bist:
  - lasse Künstler leer
  - lasse Titel leer
  - lasse Jahr leer
- Künstler nur eintragen, wenn:
  - eindeutige Signatur sichtbar
  ODER
  - das Werk extrem bekannt und eindeutig identifizierbar ist.

- Maße niemals schätzen.
- Standort niemals erfinden.
- Rechte niemals erfinden.

- Technik nur vorsichtig formulieren.
- Beschreibung sachlich formulieren.

- Schlagworte sollen möglichst enthalten:
  - Künstlername (wenn vorhanden)
  - Bildtitel (wenn vorhanden)
  - Motiv
  - Stil
  - Technik
  - Gattung

Gib ausschließlich gültiges JSON zurück.

Schema:
{
  "kuenstler": "",
  "titel": "",
  "jahr": "",
  "technik": "",
  "beschreibung": "",
  "schlagworte": "",
  "einschaetzung": "sicher / wahrscheinlich / unsicher",
  "begruendung": "",
  "hinweise": ""
}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": prompt
                    },
                    {
                        "type": "input_image",
                        "image_url": data_url
                    },
                ],
            }
        ],
    )

    text = response.output_text.strip()

    try:

        return json.loads(text)

    except:

        return {
            "kuenstler": "",
            "titel": "",
            "jahr": "",
            "technik": "",
            "beschreibung": text,
            "schlagworte": "",
            "einschaetzung": "unsicher",
            "begruendung": "JSON konnte nicht gelesen werden",
            "hinweise": ""
        }


def bild_nach_supabase(
    uploaded_file
):

    suffix = Path(
        uploaded_file.name
    ).suffix

    eindeutiger_name = (
        f"{uuid.uuid4()}{suffix}"
    )

    file_bytes = (
        uploaded_file.getvalue()
    )

    supabase.storage.from_(
        SUPABASE_BUCKET
    ).upload(
        eindeutiger_name,
        file_bytes,
        {
            "content-type":
            uploaded_file.type
        },
    )

    public_url = (
        supabase.storage.from_(
            SUPABASE_BUCKET
        ).get_public_url(
            eindeutiger_name
        )
    )

    return (
        eindeutiger_name,
        public_url
    )


with st.sidebar:

    st.header("Navigation")

    seite = st.radio(
        "Bereich wählen",
        [
            "Archiv durchsuchen",
            "Neues Bild hinzufügen"
        ],
        index=0 if st.session_state["seite"] == "Archiv durchsuchen" else 1,
    )

    st.session_state["seite"] = seite

    st.divider()

    if st.button("Abmelden"):

        st.session_state["eingeloggt"] = False

        st.rerun()


if st.session_state["seite"] == "Neues Bild hinzufügen":

    st.header(
        "Neue Bilder hinzufügen"
    )

    uploaded_files = st.file_uploader(
        "Bilddateien auswählen",
        type=[
            "jpg",
            "jpeg",
            "png",
            "webp",
            "tif",
            "tiff"
        ],
        accept_multiple_files=True,
    )

    analyse = st.session_state.get(
        "ki_upload_analyse",
        {}
    )

    kuenstler_neu = st.text_input(
        "Künstler",
        value=analyse.get(
            "kuenstler",
            ""
        )
    )

    titel_neu = st.text_input(
        "Titel",
        value=analyse.get(
            "titel",
            ""
        )
    )

    jahr_neu = st.text_input(
        "Jahr",
        value=analyse.get(
            "jahr",
            ""
        )
    )

    technik_neu = st.text_input(
        "Technik",
        value=analyse.get(
            "technik",
            ""
        )
    )

    masse_neu = st.text_input(
        "Maße"
    )

    standort_neu = st.text_input(
        "Standort"
    )

    rechte_neu = st.text_input(
        "Rechte"
    )

    beschreibung_neu = st.text_area(
        "Beschreibung",
        value=analyse.get(
            "beschreibung",
            ""
        )
    )

    schlagworte_neu = st.text_input(
        "Schlagworte",
        value=analyse.get(
            "schlagworte",
            ""
        )
    )

    if analyse:

        st.info(
            f"Einschätzung der KI: "
            f"{analyse.get('einschaetzung', '')}"
        )

        st.caption(
            analyse.get(
                "begruendung",
                ""
            )
        )

        if analyse.get("hinweise"):

            st.warning(
                analyse.get(
                    "hinweise",
                    ""
                )
            )

        if st.button(
            "KI-Vorschlag verwerfen"
        ):

            st.session_state[
                "ki_upload_analyse"
            ] = {}

            st.rerun()

    if uploaded_files:

        st.write(
            f"{len(uploaded_files)} Bilddatei(en) ausgewählt"
        )

        if st.button(
            "KI-Recherche für erstes Bild starten"
        ):

            erste_datei = uploaded_files[0]

            with st.spinner(
                "KI analysiert das Bild..."
            ):

                try:

                    analyse = (
                        ki_recherche_fuer_bild(
                            erste_datei
                        )
                    )

                    st.session_state[
                        "ki_upload_analyse"
                    ] = analyse

                    st.rerun()

                except Exception as e:

                    st.error(
                        f"Fehler bei der KI-Recherche: {e}"
                    )

        vorschau_spalten = st.columns(4)

        for index, datei in enumerate(uploaded_files):

            with vorschau_spalten[index % 4]:

                st.image(
                    datei,
                    width=150
                )

                st.caption(
                    datei.name
                )

    if st.button(
        "Bilder und Datensätze speichern"
    ):

        if not uploaded_files:

            st.error(
                "Bitte zuerst Bilddateien auswählen."
            )

        else:

            gespeichert = 0

            for uploaded_file in uploaded_files:

                (
                    eindeutiger_name,
                    public_url
                ) = bild_nach_supabase(
                    uploaded_file
                )

                daten = {
                    "dateiname":
                    eindeutiger_name,

                    "kuenstler":
                    kuenstler_neu,

                    "titel":
                    titel_neu if titel_neu
                    else Path(
                        uploaded_file.name
                    ).stem,

                    "jahr":
                    jahr_neu,

                    "technik":
                    technik_neu,

                    "masse":
                    masse_neu,

                    "standort":
                    standort_neu,

                    "rechte":
                    rechte_neu,

                    "beschreibung":
                    beschreibung_neu,

                    "schlagworte":
                    schlagworte_neu,

                    "bildpfad":
                    public_url,
                }

                datensatz_speichern(
                    daten
                )

                gespeichert += 1

            st.session_state[
                "ki_upload_analyse"
            ] = {}

            st.success(
                f"{gespeichert} Bilder gespeichert."
            )

            st.session_state["seite"] = (
                "Archiv durchsuchen"
            )

            st.rerun()


else:

    st.info(
        "Archivansicht unverändert."
    )