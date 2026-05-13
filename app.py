import streamlit as st
import pandas as pd
import base64
import json
import uuid
import requests
from pathlib import Path
from io import BytesIO
from PIL import Image
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

if not st.session_state["eingeloggt"]:
    login_pruefen()
    st.stop()


st.title("Kunstbild-Datenbank")
st.caption("Recherche, Vorschau, Upload, Export, KI-Analyse und Verwaltung deiner Kunstbilder")


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


def bild_als_base64_data_url(bild_url):
    response = requests.get(bild_url, timeout=30)
    encoded = base64.b64encode(response.content).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def ki_bildanalyse(bild_url):
    api_key = st.secrets.get("OPENAI_API_KEY", "")
    client = OpenAI(api_key=api_key)

    data_url = bild_als_base64_data_url(bild_url)

    prompt = """
Analysiere das Kunstbild für ein deutschsprachiges Kunstarchiv.

Gib ausschließlich gültiges JSON zurück, ohne Markdown.

Schema:
{
  "beschreibung": "Ein sachlicher Beschreibungstext mit 3 bis 5 Sätzen.",
  "schlagworte": "8 bis 12 Schlagworte, kommasepariert",
  "technik_stil": "Vorsichtige Einschätzung zu Technik, Stil, Gattung oder Bildtyp."
}

Wichtig:
- Keine erfundenen Künstlernamen.
- Keine erfundenen Datierungen.
- Bei Unsicherheit vorsichtig formulieren.
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
        }
def ki_recherche_fuer_bild(uploaded_file):

    prompt = """
Du bist Kunsthistoriker, Archivar und Bildrechercheur.

Analysiere das hochgeladene Kunstwerk.

WICHTIG:
- Erfinde niemals Künstlernamen.
- Erfinde niemals Bildtitel.
- Erfinde niemals Datierungen.
- Wenn du unsicher bist, formuliere das klar.
- Gib nur Informationen an, die plausibel sind.

Nutze:
- Bildanalyse
- kunsthistorische Stilmerkmale
- sichtbare Signaturen
- Motivik
- mögliche Internetrecherchehinweise

Gib ausschließlich gültiges JSON zurück.

Schema:
{
  "kuenstler": "...",
  "titel": "...",
  "jahr": "...",
  "technik": "...",
  "beschreibung": "...",
  "schlagworte": "...",
  "einschaetzung": "sicher / wahrscheinlich / unsicher",
  "begruendung": "..."
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
            "begruendung": "JSON konnte nicht gelesen werden"
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

    uploaded_files = st.file_uploader(
        "Bilddateien auswählen",
        type=["jpg", "jpeg", "png", "webp", "tif", "tiff"],
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
    masse_neu = st.text_input("Maße")
    standort_neu = st.text_input("Standort")
    rechte_neu = st.text_input("Rechte")
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

    if uploaded_files:
	 if st.button(
            "KI-Recherche starten"
        ):

            erste_datei = uploaded_files[0]

            with st.spinner(
                "KI analysiert das Bild..."
            ):

                analyse = ki_recherche_fuer_bild(
                    erste_datei
                )

                st.session_state[
                    "ki_upload_analyse"
                ] = analyse

        st.write(f"{len(uploaded_files)} Bilddatei(en) ausgewählt")

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
                }

                datensatz_speichern(daten)
                gespeichert += 1

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
                        st.image(
                            bild_url,
                            width=260,
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

            auswahl = st.selectbox("Werk auswählen", auswahl_liste, index=vorauswahl_index)
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
                st.write(f"**Beschreibung:** {row.get('beschreibung', '')}")
                st.write(f"**Schlagworte:** {row.get('schlagworte', '')}")

                st.divider()

                with st.expander("KI-Bildanalyse"):
                    if st.button("KI-Beschreibung erzeugen", key=f"ki_{datensatz_id}"):
                        with st.spinner("KI analysiert das Bild..."):
                            try:
                                analyse = ki_bildanalyse(bild_url)

                                st.session_state[f"ki_beschreibung_{datensatz_id}"] = analyse.get("beschreibung", "")
                                st.session_state[f"ki_schlagworte_{datensatz_id}"] = analyse.get("schlagworte", "")
                                st.session_state[f"ki_technik_{datensatz_id}"] = analyse.get("technik_stil", "")

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