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

STIL_OPTIONEN = [
    "Renaissance",
    "Barock",
    "Klassizismus",
    "Romantik",
    "Realismus",
    "Impressionismus",
    "Expressionismus",
    "Kubismus",
    "Fauvismus",
    "Surrealismus",
    "Abstrakte Kunst",
    "Pop Art",
    "Fotorealismus",
    "Neue Sachlichkeit",
    "Verismus",
    "Symbolismus",
    "Jugendstil",
    "Dadaismus",
    "Konstruktivismus",
    "Minimalismus",
    "Konzeptkunst",
    "Informel",
    "Tachismus",
    "Arte Povera",
    "Op Art",
    "Land Art",
    "Street Art",
    "Zeitgenössische Kunst",
]

TECHNIK_OPTIONEN = [
    "Ölmalerei",
    "Acrylmalerei",
    "Aquarellmalerei",
    "Pastellmalerei",
    "Gouache",
    "Tempera",
    "Mischtechnik",
    "Collage",
    "Tusche",
    "Zeichnung",
    "Kohle",
    "Radierung",
    "Lithografie",
    "Siebdruck",
    "Fotografie",
    "Digitale Kunst",
]

GATTUNG_OPTIONEN = [
    "Porträt",
    "Selbstporträt",
    "Landschaft",
    "Stadtansicht",
    "Stillleben",
    "Akt",
    "Interieur",
    "Tierdarstellung",
    "Historienbild",
    "Religiöses Motiv",
    "Abstrakt",
    "Architektur",
    "Naturdarstellung",
    "Gesellschaftsszene",
]


st.set_page_config(page_title="Kunstbild-Datenbank", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_BUCKET = st.secrets["SUPABASE_BUCKET"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.markdown(
    """
    <style>
    .fixed-image-box {
        width: 100%;
        height: 260px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f7f7f7;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 0.75rem;
    }

    .fixed-image-box img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }

    .stButton > button {
        width: 100%;
    }

    .stDownloadButton > button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def login_pruefen():
    st.title("Kunstbild-Datenbank")
    st.subheader("Geschützter Zugang")
    eingabe = st.text_input("Passwort eingeben", type="password")

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
st.caption("Recherche, Vorschau, Upload, Export, KI-Analyse und Verwaltung deiner Kunstbilder")


def text_zu_liste(text):
    if not text:
        return []

    return [
        eintrag.strip()
        for eintrag in str(text).split(",")
        if eintrag.strip()
    ]


def liste_zu_text(liste):
    return ", ".join(liste)


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
                "stile",
                "techniken",
                "gattungen",
            ]
        )

    for spalte in ["stile", "techniken", "gattungen"]:
        if spalte not in df.columns:
            df[spalte] = ""

    return df.fillna("")


def excel_export_erzeugen(df):
    export_df = df.drop(columns=["id"], errors="ignore")
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Kunstbilder")

    output.seek(0)
    return output


def datensatz_speichern(daten):
    supabase.table("kunstbilder").insert(daten).execute()


def datensatz_aktualisieren(datensatz_id, daten):
    url = f"{SUPABASE_URL}/rest/v1/kunstbilder?id=eq.{int(datensatz_id)}"

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    payload = {
        "kuenstler": str(daten.get("kuenstler", "")),
        "titel": str(daten.get("titel", "")),
        "jahr": str(daten.get("jahr", "")),
        "technik": str(daten.get("technik", "")),
        "masse": str(daten.get("masse", "")),
        "standort": str(daten.get("standort", "")),
        "rechte": str(daten.get("rechte", "")),
        "beschreibung": str(daten.get("beschreibung", "")),
        "schlagworte": str(daten.get("schlagworte", "")),
        "stile": str(daten.get("stile", "")),
        "techniken": str(daten.get("techniken", "")),
        "gattungen": str(daten.get("gattungen", "")),
    }

    response = requests.patch(
        url,
        headers=headers,
        json=payload,
        timeout=30,
    )

    if response.status_code not in (200, 204):
        raise RuntimeError(
            f"Supabase-Update fehlgeschlagen: {response.status_code} - {response.text}"
        )


def datensatz_loeschen(datensatz_id, dateiname):
    try:
        supabase.storage.from_(SUPABASE_BUCKET).remove([str(dateiname)])
    except Exception:
        pass

    supabase.table("kunstbilder").delete().eq("id", datensatz_id).execute()


def kurzer_titel(text, max_laenge=18):
    text = str(text)
    if len(text) > max_laenge:
        return text[:max_laenge] + "..."
    return text


def bild_als_base64_data_url_from_url(bild_url):
    response = requests.get(bild_url, timeout=30)
    encoded = base64.b64encode(response.content).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def bild_als_base64_data_url_from_upload(uploaded_file):
    file_bytes = uploaded_file.getvalue()
    encoded = base64.b64encode(file_bytes).decode("utf-8")
    mime_type = uploaded_file.type or "image/jpeg"
    return f"data:{mime_type};base64,{encoded}"


def ki_textgenerator_upload(uploaded_file, kuenstler, titel, jahr):
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key)

    data_url = bild_als_base64_data_url_from_upload(uploaded_file)

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
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
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


def ki_bildanalyse_detail(bild_url, kuenstler, titel, jahr):
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key)

    data_url = bild_als_base64_data_url_from_url(bild_url)

    prompt = f"""
Du bist Kunsthistoriker und Museumsredakteur.

Analysiere das Kunstwerk.

Bekannte Angaben:
Künstler: {kuenstler}
Titel: {titel}
Jahr: {jahr}

Aufgabe:
- Formuliere eine sachliche Beschreibung mit 3 bis 5 Sätzen.
- Erzeuge 8 bis 12 Schlagworte.
- Schätze Technik, Stil oder Gattung vorsichtig ein.
- Wähle passende Stile/Epochen ausschließlich aus dieser Liste:
{", ".join(STIL_OPTIONEN)}
- Wähle passende Techniken ausschließlich aus dieser Liste:
{", ".join(TECHNIK_OPTIONEN)}
- Wähle passende Gattungen/Motive ausschließlich aus dieser Liste:
{", ".join(GATTUNG_OPTIONEN)}
- Keine erfundenen Künstlernamen.
- Keine erfundenen Datierungen.
- Schlagworte sollen Künstler und Titel enthalten, sofern angegeben.

Gib ausschließlich gültiges JSON zurück, ohne Markdown.

Schema:
{{
  "beschreibung": "",
  "schlagworte": "",
  "technik_stil": "",
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
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            }
        ],
    )

    text = response.output_text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {
            "beschreibung": text,
            "schlagworte": "",
            "technik_stil": "",
            "stile": "",
            "techniken": "",
            "gattungen": "",
        }


def bild_nach_supabase(uploaded_file):
    suffix = Path(uploaded_file.name).suffix
    eindeutiger_name = f"{uuid.uuid4()}{suffix}"

    file_bytes = uploaded_file.getvalue()

    supabase.storage.from_(SUPABASE_BUCKET).upload(
        eindeutiger_name,
        file_bytes,
        {"content-type": uploaded_file.type},
    )

    public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(eindeutiger_name)

    return eindeutiger_name, public_url


def bild_html(url):
    return f"""
    <div class="fixed-image-box">
        <img src="{url}">
    </div>
    """


with st.sidebar:
    st.header("Navigation")

    seite = st.radio(
        "Bereich wählen",
        ["Archiv durchsuchen", "Neues Bild hinzufügen"],
        index=0 if st.session_state["seite"] == "Archiv durchsuchen" else 1,
    )

    st.session_state["seite"] = seite

    st.divider()

    if st.button("Abmelden"):
        st.session_state["eingeloggt"] = False
        st.rerun()


if st.session_state["seite"] == "Neues Bild hinzufügen":
    st.header("Neue Bilder hinzufügen")

    if st.button("← Zurück zum Archiv"):
        st.session_state["seite"] = "Archiv durchsuchen"
        st.session_state["ansicht"] = "Galerieansicht"
        st.rerun()

    uploaded_files = st.file_uploader(
        "Bilddateien auswählen",
        type=["jpg", "jpeg", "png", "webp", "tif", "tiff"],
        accept_multiple_files=True,
    )

    analyse = st.session_state.get("ki_upload_analyse", {})

    kuenstler_neu = st.text_input("Künstler")
    titel_neu = st.text_input("Titel")
    jahr_neu = st.text_input("Jahr")

    technik_neu = st.text_input(
        "Technik",
        value=analyse.get("technik", ""),
    )

    stile_neu = st.multiselect(
        "Stil / Epoche",
        STIL_OPTIONEN,
        default=text_zu_liste(analyse.get("stile", "")),
    )

    techniken_neu = st.multiselect(
        "Techniken",
        TECHNIK_OPTIONEN,
        default=text_zu_liste(analyse.get("techniken", "")),
    )

    gattungen_neu = st.multiselect(
        "Gattung / Motiv",
        GATTUNG_OPTIONEN,
        default=text_zu_liste(analyse.get("gattungen", "")),
    )

    masse_neu = st.text_input("Maße")
    standort_neu = st.text_input("Standort")
    rechte_neu = st.text_input("Rechte")

    beschreibung_neu = st.text_area(
        "Beschreibung",
        value=analyse.get("beschreibung", ""),
    )

    schlagworte_neu = st.text_input(
        "Schlagworte",
        value=analyse.get("schlagworte", ""),
    )

    if uploaded_files:
        st.write(f"{len(uploaded_files)} Bilddatei(en) ausgewählt")

        if st.button("Beschreibung, Schlagworte und Kategorien erzeugen"):
            erste_datei = uploaded_files[0]

            with st.spinner("KI analysiert das Bild..."):
                try:
                    analyse = ki_textgenerator_upload(
                        erste_datei,
                        kuenstler_neu,
                        titel_neu,
                        jahr_neu,
                    )

                    st.session_state["ki_upload_analyse"] = analyse
                    st.rerun()

                except Exception as e:
                    st.error(f"Fehler bei der KI-Analyse: {e}")

        vorschau_spalten = st.columns(4)

        for index, datei in enumerate(uploaded_files):
            with vorschau_spalten[index % 4]:
                st.image(datei, width=150)
                st.caption(datei.name)

    if st.button("Bilder und Datensätze speichern"):
        if not uploaded_files:
            st.error("Bitte zuerst Bilddateien auswählen.")
        else:
            gespeichert = 0

            for uploaded_file in uploaded_files:
                eindeutiger_name, public_url = bild_nach_supabase(uploaded_file)

                daten = {
                    "dateiname": eindeutiger_name,
                    "kuenstler": kuenstler_neu,
                    "titel": titel_neu if titel_neu else Path(uploaded_file.name).stem,
                    "jahr": jahr_neu,
                    "technik": technik_neu,
                    "masse": masse_neu,
                    "standort": standort_neu,
                    "rechte": rechte_neu,
                    "beschreibung": beschreibung_neu,
                    "schlagworte": schlagworte_neu,
                    "bildpfad": public_url,
                    "stile": liste_zu_text(stile_neu),
                    "techniken": liste_zu_text(techniken_neu),
                    "gattungen": liste_zu_text(gattungen_neu),
                }

                datensatz_speichern(daten)
                gespeichert += 1

            st.session_state["ki_upload_analyse"] = {}
            st.session_state["seite"] = "Archiv durchsuchen"
            st.session_state["ansicht"] = "Galerieansicht"
            st.success(f"{gespeichert} Bilder gespeichert.")
            st.rerun()


else:
    df = daten_laden()

    st.sidebar.header("Filter")

    suchbegriff = st.sidebar.text_input("Freie Suche")

    kuenstler_liste = ["Alle"] + sorted(df["kuenstler"].astype(str).unique().tolist())
    kuenstler_filter = st.sidebar.selectbox("Künstler", kuenstler_liste)

    stil_filter = st.sidebar.multiselect(
        "Stil / Epoche",
        STIL_OPTIONEN,
    )

    technik_filter = st.sidebar.multiselect(
        "Techniken",
        TECHNIK_OPTIONEN,
    )

    gattung_filter = st.sidebar.multiselect(
        "Gattung / Motiv",
        GATTUNG_OPTIONEN,
    )

    sortierung = st.sidebar.selectbox(
        "Sortieren nach",
        ["titel", "kuenstler", "jahr", "technik"],
    )

    gefiltert = df.copy()

    if suchbegriff:
        suchbegriff = suchbegriff.lower()
        gefiltert = gefiltert[
            gefiltert.astype(str)
            .apply(lambda row: row.str.lower().str.contains(suchbegriff).any(), axis=1)
        ]

    if kuenstler_filter != "Alle":
        gefiltert = gefiltert[gefiltert["kuenstler"].astype(str) == kuenstler_filter]

    if stil_filter:
        gefiltert = gefiltert[
            gefiltert["stile"].astype(str).apply(
                lambda text: any(wert in text for wert in stil_filter)
            )
        ]

    if technik_filter:
        gefiltert = gefiltert[
            gefiltert["techniken"].astype(str).apply(
                lambda text: any(wert in text for wert in technik_filter)
            )
        ]

    if gattung_filter:
        gefiltert = gefiltert[
            gefiltert["gattungen"].astype(str).apply(
                lambda text: any(wert in text for wert in gattung_filter)
            )
        ]

    if sortierung in gefiltert.columns:
        gefiltert = gefiltert.sort_values(by=sortierung, ascending=True)

    gefiltert = gefiltert.reset_index(drop=True)

    st.write(f"**{len(gefiltert)} Einträge gefunden**")

    export_excel = excel_export_erzeugen(gefiltert)
    export_csv = (
        gefiltert.drop(columns=["id"], errors="ignore")
        .to_csv(index=False)
        .encode("utf-8-sig")
    )

    col_export1, col_export2 = st.columns([1, 1])

    with col_export1:
        st.download_button(
            label="Trefferliste als Excel herunterladen",
            data=export_excel,
            file_name="kunstbilder_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col_export2:
        st.download_button(
            label="Trefferliste als CSV herunterladen",
            data=export_csv,
            file_name="kunstbilder_export.csv",
            mime="text/csv",
        )

    ansicht = st.radio(
        "Ansicht",
        ["Galerieansicht", "Detailansicht"],
        horizontal=True,
        index=0 if st.session_state["ansicht"] == "Galerieansicht" else 1,
    )

    st.session_state["ansicht"] = ansicht

    if ansicht == "Galerieansicht":
        for start in range(0, len(gefiltert), 3):
            spalten = st.columns(3)

            for i in range(3):
                if start + i >= len(gefiltert):
                    continue

                row = gefiltert.iloc[start + i]
                bild_url = row["bildpfad"]

                with spalten[i]:
                    with st.container(border=True):
                        st.markdown(
                            bild_html(bild_url),
                            unsafe_allow_html=True,
                        )

                        if st.button("Groß anzeigen", key=f"gross_{row['id']}"):
                            st.session_state["ausgewaehlte_id"] = int(row["id"])
                            st.session_state["ansicht"] = "Detailansicht"
                            st.rerun()

                        try:
                            bild_download = requests.get(bild_url, timeout=20).content
                            st.download_button(
                                label="Bild herunterladen",
                                data=bild_download,
                                file_name=str(row["dateiname"]),
                                mime="application/octet-stream",
                                key=f"download_{row['id']}",
                            )
                        except Exception:
                            st.info("Download aktuell nicht verfügbar.")

                        with st.popover("🗑️ Löschen"):
                            st.warning("Wirklich löschen?")

                            if st.button(
                                "Ja, endgültig löschen",
                                key=f"confirm_delete_gallery_{row['id']}",
                            ):
                                datensatz_loeschen(
                                    row["id"],
                                    row["dateiname"],
                                )
                                st.success("Datensatz wurde gelöscht.")
                                st.rerun()

                        st.markdown(f"### {kurzer_titel(row.get('titel', ''))}")
                        st.write(f"**Künstler:** {row.get('kuenstler', '')}")
                        st.write(f"**Jahr:** {row.get('jahr', '')}")

                        if row.get("stile", ""):
                            st.caption(f"Stil: {row.get('stile', '')}")

                        if row.get("gattungen", ""):
                            st.caption(f"Gattung: {row.get('gattungen', '')}")

    else:
        auswahl_liste = [
            f"{row.get('kuenstler', '')} – {row.get('titel', '')} [{row.get('id', '')}]"
            for _, row in gefiltert.iterrows()
        ]

        if len(auswahl_liste) == 0:
            st.info("Keine Einträge gefunden.")
        else:
            vorauswahl_index = 0

            if st.session_state["ausgewaehlte_id"] is not None:
                for idx, row_check in gefiltert.iterrows():
                    if int(row_check["id"]) == int(st.session_state["ausgewaehlte_id"]):
                        vorauswahl_index = idx
                        break

            auswahl = st.selectbox(
                "Werk auswählen",
                auswahl_liste,
                index=vorauswahl_index,
            )

            index = auswahl_liste.index(auswahl)

            row = gefiltert.iloc[index]
            datensatz_id = int(row["id"])

            st.session_state["ausgewaehlte_id"] = datensatz_id

            bild_url = row["bildpfad"]

            if st.button("Zurück zur Galerie"):
                st.session_state["ansicht"] = "Galerieansicht"
                st.rerun()

            col1, col2 = st.columns([1.4, 1])

            with col1:
                st.image(bild_url, use_container_width=True)

                try:
                    bild_download = requests.get(bild_url, timeout=20).content
                    st.download_button(
                        label="Bild herunterladen",
                        data=bild_download,
                        file_name=str(row["dateiname"]),
                        mime="application/octet-stream",
                        key=f"detail_download_{datensatz_id}",
                    )
                except Exception:
                    st.info("Download aktuell nicht verfügbar.")

            with col2:
                st.header(str(row.get("titel", "")))

                st.write(f"**Künstler:** {row.get('kuenstler', '')}")
                st.write(f"**Jahr:** {row.get('jahr', '')}")
                st.write(f"**Technik:** {row.get('technik', '')}")
                st.write(f"**Maße:** {row.get('masse', '')}")
                st.write(f"**Standort:** {row.get('standort', '')}")
                st.write(f"**Rechte:** {row.get('rechte', '')}")
                st.write(f"**Stil / Epoche:** {row.get('stile', '')}")
                st.write(f"**Techniken:** {row.get('techniken', '')}")
                st.write(f"**Gattung / Motiv:** {row.get('gattungen', '')}")
                st.write(f"**Beschreibung:** {row.get('beschreibung', '')}")
                st.write(f"**Schlagworte:** {row.get('schlagworte', '')}")

                st.divider()

                with st.expander("KI-Bildanalyse"):
                    if st.button("KI-Beschreibung erzeugen", key=f"ki_{datensatz_id}"):
                        with st.spinner("KI analysiert das Bild..."):
                            try:
                                analyse = ki_bildanalyse_detail(
                                    bild_url,
                                    str(row.get("kuenstler", "")),
                                    str(row.get("titel", "")),
                                    str(row.get("jahr", "")),
                                )

                                st.session_state[f"ki_beschreibung_{datensatz_id}"] = analyse.get("beschreibung", "")
                                st.session_state[f"ki_schlagworte_{datensatz_id}"] = analyse.get("schlagworte", "")
                                st.session_state[f"ki_technik_{datensatz_id}"] = analyse.get("technik_stil", "")
                                st.session_state[f"ki_stile_{datensatz_id}"] = analyse.get("stile", "")
                                st.session_state[f"ki_techniken_{datensatz_id}"] = analyse.get("techniken", "")
                                st.session_state[f"ki_gattungen_{datensatz_id}"] = analyse.get("gattungen", "")

                            except Exception as e:
                                st.error(f"Fehler bei der KI-Analyse: {e}")

                    if st.session_state.get(f"ki_beschreibung_{datensatz_id}"):
                        st.subheader("KI-Vorschlag")

                        st.write("**Beschreibung:**")
                        st.write(st.session_state[f"ki_beschreibung_{datensatz_id}"])

                        st.write("**Schlagworte:**")
                        st.write(st.session_state[f"ki_schlagworte_{datensatz_id}"])

                        st.write("**Technik/Stil:**")
                        st.write(st.session_state[f"ki_technik_{datensatz_id}"])

                        st.write("**Stil / Epoche:**")
                        st.write(st.session_state[f"ki_stile_{datensatz_id}"])

                        st.write("**Techniken:**")
                        st.write(st.session_state[f"ki_techniken_{datensatz_id}"])

                        st.write("**Gattung / Motiv:**")
                        st.write(st.session_state[f"ki_gattungen_{datensatz_id}"])

                        if st.button(
                            "KI-Vorschlag in Datensatz übernehmen",
                            key=f"ki_uebernehmen_{datensatz_id}",
                        ):
                            neue_daten = {
                                "kuenstler": str(row.get("kuenstler", "")),
                                "titel": str(row.get("titel", "")),
                                "jahr": str(row.get("jahr", "")),
                                "technik": st.session_state[f"ki_technik_{datensatz_id}"],
                                "masse": str(row.get("masse", "")),
                                "standort": str(row.get("standort", "")),
                                "rechte": str(row.get("rechte", "")),
                                "beschreibung": st.session_state[f"ki_beschreibung_{datensatz_id}"],
                                "schlagworte": st.session_state[f"ki_schlagworte_{datensatz_id}"],
                                "stile": st.session_state[f"ki_stile_{datensatz_id}"],
                                "techniken": st.session_state[f"ki_techniken_{datensatz_id}"],
                                "gattungen": st.session_state[f"ki_gattungen_{datensatz_id}"],
                            }

                            datensatz_aktualisieren(datensatz_id, neue_daten)
                            st.success("KI-Vorschlag wurde übernommen.")
                            st.rerun()

                st.divider()

                with st.expander("Datensatz bearbeiten"):
                    with st.form(key=f"bearbeiten_form_{datensatz_id}"):
                        bearb_kuenstler = st.text_input("Künstler", value=str(row.get("kuenstler", "")))
                        bearb_titel = st.text_input("Titel", value=str(row.get("titel", "")))
                        bearb_jahr = st.text_input("Jahr", value=str(row.get("jahr", "")))
                        bearb_technik = st.text_input("Technik", value=str(row.get("technik", "")))
                        bearb_masse = st.text_input("Maße", value=str(row.get("masse", "")))
                        bearb_standort = st.text_input("Standort", value=str(row.get("standort", "")))
                        bearb_rechte = st.text_input("Rechte", value=str(row.get("rechte", "")))

                        bearb_stile = st.multiselect(
                            "Stil / Epoche",
                            STIL_OPTIONEN,
                            default=text_zu_liste(row.get("stile", "")),
                        )

                        bearb_techniken = st.multiselect(
                            "Techniken",
                            TECHNIK_OPTIONEN,
                            default=text_zu_liste(row.get("techniken", "")),
                        )

                        bearb_gattungen = st.multiselect(
                            "Gattung / Motiv",
                            GATTUNG_OPTIONEN,
                            default=text_zu_liste(row.get("gattungen", "")),
                        )

                        bearb_beschreibung = st.text_area("Beschreibung", value=str(row.get("beschreibung", "")))
                        bearb_schlagworte = st.text_input("Schlagworte", value=str(row.get("schlagworte", "")))

                        speichern = st.form_submit_button("Änderungen speichern")

                    if speichern:
                        neue_daten = {
                            "kuenstler": bearb_kuenstler,
                            "titel": bearb_titel,
                            "jahr": bearb_jahr,
                            "technik": bearb_technik,
                            "masse": bearb_masse,
                            "standort": bearb_standort,
                            "rechte": bearb_rechte,
                            "beschreibung": bearb_beschreibung,
                            "schlagworte": bearb_schlagworte,
                            "stile": liste_zu_text(bearb_stile),
                            "techniken": liste_zu_text(bearb_techniken),
                            "gattungen": liste_zu_text(bearb_gattungen),
                        }

                        try:
                            datensatz_aktualisieren(datensatz_id, neue_daten)
                            st.success("Änderungen wurden gespeichert.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Fehler beim Speichern: {e}")

                st.divider()

                loeschen_bestaetigen = st.checkbox(
                    "Ich möchte diesen Datensatz wirklich löschen.",
                    key=f"loeschen_check_{datensatz_id}",
                )

                if st.button("Datensatz löschen", type="primary", key=f"loeschen_{datensatz_id}"):
                    if loeschen_bestaetigen:
                        datensatz_loeschen(datensatz_id, row["dateiname"])
                        st.success("Datensatz wurde gelöscht.")
                        st.rerun()
                    else:
                        st.error("Bitte zuerst die Löschung bestätigen.")