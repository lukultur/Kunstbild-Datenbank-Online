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

st.set_page_config(
    page_title="Kunstbild-Datenbank",
    layout="wide"
)

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_BUCKET = st.secrets["SUPABASE_BUCKET"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

st.markdown(
    """
    <style>

    .stButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-size: 0.95rem;
    }

    .stDownloadButton > button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        font-size: 0.95rem;
    }

    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


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

if not st.session_state["eingeloggt"]:

    login_pruefen()

    st.stop()


st.title("Kunstbild-Datenbank")

st.caption(
    "Recherche, Vorschau, Upload, KI-Analyse und Verwaltung deiner Kunstbilder"
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
    max_laenge=24
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


def ki_bildanalyse(
    bild_url
):

    api_key = st.secrets.get(
        "OPENAI_API_KEY",
        ""
    )

    client = OpenAI(
        api_key=api_key
    )

    data_url = (
        bild_als_base64_data_url(
            bild_url
        )
    )

    prompt = """
Analysiere das Kunstbild für ein deutschsprachiges Kunstarchiv.

Gib ausschließlich gültiges JSON zurück.

Schema:
{
  "beschreibung": "...",
  "schlagworte": "...",
  "technik_stil": "..."
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
            "beschreibung": text,
            "schlagworte": "",
            "technik_stil": "",
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

    kuenstler_neu = st.text_input(
        "Künstler"
    )

    titel_neu = st.text_input(
        "Titel"
    )

    jahr_neu = st.text_input(
        "Jahr"
    )

    technik_neu = st.text_input(
        "Technik"
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
        "Beschreibung"
    )

    schlagworte_neu = st.text_input(
        "Schlagworte"
    )

    if uploaded_files:

        st.success(
            f"{len(uploaded_files)} Bilddatei(en) ausgewählt"
        )

        cols = st.columns(2)

        for index, datei in enumerate(uploaded_files):

            with cols[index % 2]:

                st.image(
                    datei,
                    use_container_width=True
                )

                st.caption(
                    datei.name
                )

    if st.button(
        "Bilder speichern"
    ):

        if not uploaded_files:

            st.error(
                "Bitte zuerst Bilder auswählen."
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

            st.success(
                f"{gespeichert} Bilder gespeichert."
            )

            st.session_state["seite"] = (
                "Archiv durchsuchen"
            )

            st.rerun()


else:

    df = daten_laden()

    with st.expander(
        "Filter und Suche"
    ):

        suchbegriff = st.text_input(
            "Freie Suche"
        )

        kuenstler_liste = (
            ["Alle"]
            +
            sorted(
                df["kuenstler"]
                .astype(str)
                .unique()
                .tolist()
            )
        )

        kuenstler_filter = (
            st.selectbox(
                "Künstler",
                kuenstler_liste
            )
        )

    gefiltert = df.copy()

    if suchbegriff:

        suchbegriff = (
            suchbegriff.lower()
        )

        gefiltert = gefiltert[
            gefiltert.astype(str)
            .apply(
                lambda row:
                row.str.lower()
                .str.contains(
                    suchbegriff
                )
                .any(),
                axis=1,
            )
        ]

    if kuenstler_filter != "Alle":

        gefiltert = gefiltert[
            gefiltert["kuenstler"]
            .astype(str)
            ==
            kuenstler_filter
        ]

    gefiltert = (
        gefiltert
        .sort_values(
            by="titel"
        )
        .reset_index(drop=True)
    )

    st.write(
        f"**{len(gefiltert)} Werke gefunden**"
    )

    ansicht = st.radio(
        "Ansicht",
        [
            "Galerie",
            "Detail"
        ],
        horizontal=True,
    )

    if ansicht == "Galerie":

        spaltenzahl = 2

        if len(gefiltert) < 3:
            spaltenzahl = 1

        for start in range(
            0,
            len(gefiltert),
            spaltenzahl
        ):

            spalten = st.columns(
                spaltenzahl
            )

            for i in range(
                spaltenzahl
            ):

                if (
                    start + i
                    >=
                    len(gefiltert)
                ):
                    continue

                row = gefiltert.iloc[
                    start + i
                ]

                with spalten[i]:

                    with st.container(
                        border=True
                    ):

                        st.image(
                            row["bildpfad"],
                            use_container_width=True
                        )

                        st.markdown(
                            f"### "
                            f"{kurzer_titel(row['titel'])}"
                        )

                        st.write(
                            f"**{row['kuenstler']}**"
                        )

                        st.write(
                            row["jahr"]
                        )

                        if st.button(
                            "Werk öffnen",
                            key=f"open_{row['id']}"
                        ):

                            st.session_state[
                                "ausgewaehlte_id"
                            ] = row["id"]

                            st.session_state[
                                "ansicht"
                            ] = "Detail"

                            st.rerun()

    else:

        if len(gefiltert) == 0:

            st.info(
                "Keine Werke vorhanden."
            )

        else:

            if (
                st.session_state[
                    "ausgewaehlte_id"
                ]
                is None
            ):

                st.session_state[
                    "ausgewaehlte_id"
                ] = int(
                    gefiltert.iloc[0]["id"]
                )

            row = gefiltert[
                gefiltert["id"]
                ==
                st.session_state[
                    "ausgewaehlte_id"
                ]
            ].iloc[0]

            st.image(
                row["bildpfad"],
                use_container_width=True
            )

            st.header(
                row["titel"]
            )

            st.write(
                f"**Künstler:** "
                f"{row['kuenstler']}"
            )

            st.write(
                f"**Jahr:** "
                f"{row['jahr']}"
            )

            st.write(
                f"**Technik:** "
                f"{row['technik']}"
            )

            st.write(
                f"**Beschreibung:** "
                f"{row['beschreibung']}"
            )

            st.write(
                f"**Schlagworte:** "
                f"{row['schlagworte']}"
            )

            st.divider()

            with st.expander(
                "Datensatz bearbeiten"
            ):

                with st.form(
                    key=f"edit_"
                    f"{row['id']}"
                ):

                    bearb_kuenstler = (
                        st.text_input(
                            "Künstler",
                            value=row[
                                "kuenstler"
                            ]
                        )
                    )

                    bearb_titel = (
                        st.text_input(
                            "Titel",
                            value=row[
                                "titel"
                            ]
                        )
                    )

                    bearb_jahr = (
                        st.text_input(
                            "Jahr",
                            value=row[
                                "jahr"
                            ]
                        )
                    )

                    bearb_technik = (
                        st.text_input(
                            "Technik",
                            value=row[
                                "technik"
                            ]
                        )
                    )

                    bearb_beschreibung = (
                        st.text_area(
                            "Beschreibung",
                            value=row[
                                "beschreibung"
                            ]
                        )
                    )

                    bearb_schlagworte = (
                        st.text_input(
                            "Schlagworte",
                            value=row[
                                "schlagworte"
                            ]
                        )
                    )

                    speichern = (
                        st.form_submit_button(
                            "Änderungen speichern"
                        )
                    )

                if speichern:

                    daten = {
                        "kuenstler":
                        bearb_kuenstler,

                        "titel":
                        bearb_titel,

                        "jahr":
                        bearb_jahr,

                        "technik":
                        bearb_technik,

                        "beschreibung":
                        bearb_beschreibung,

                        "schlagworte":
                        bearb_schlagworte,
                    }

                    datensatz_aktualisieren(
                        row["id"],
                        daten
                    )

                    st.success(
                        "Gespeichert."
                    )

                    st.rerun()