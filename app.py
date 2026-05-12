import streamlit as st
import pandas as pd
import sqlite3
import shutil
import base64
import json
from pathlib import Path
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps
from openai import OpenAI

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "kunstbilder.db"
IMAGE_DIR = BASE_DIR / "Bilder"
BACKUP_DIR = BASE_DIR / "Backups"

PASSWORT = "kunstarchiv2026"

IMAGE_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

st.set_page_config(page_title="Kunstbild-Datenbank", layout="wide")


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

if "ausgewaehlte_rowid" not in st.session_state:
    st.session_state["ausgewaehlte_rowid"] = None

if not st.session_state["eingeloggt"]:
    login_pruefen()
    st.stop()


st.title("Kunstbild-Datenbank")
st.caption("Recherche, Vorschau, Upload, Export, KI-Analyse und Verwaltung deiner Kunstbilder")


def backup_erstellen():
    if DB_FILE.exists():
        zeit = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        ziel = BACKUP_DIR / f"kunstbilder_backup_{zeit}.db"
        shutil.copy2(DB_FILE, ziel)


def daten_laden():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT rowid, * FROM kunstbilder", conn)
    conn.close()
    return df.fillna("")


def excel_export_erzeugen(df):
    export_df = df.drop(columns=["rowid"], errors="ignore")
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        export_df.to_excel(writer, index=False, sheet_name="Kunstbilder")

    output.seek(0)
    return output


def datensatz_speichern(daten):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO kunstbilder
        ("Dateiname", "Künstler", "Titel", "Jahr", "Technik", "Maße", "Standort", "Rechte", "Beschreibung", "Schlagworte", "Bildpfad")
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            daten["Dateiname"],
            daten["Künstler"],
            daten["Titel"],
            daten["Jahr"],
            daten["Technik"],
            daten["Maße"],
            daten["Standort"],
            daten["Rechte"],
            daten["Beschreibung"],
            daten["Schlagworte"],
            daten["Bildpfad"],
        ),
    )

    conn.commit()
    conn.close()


def datensatz_aktualisieren(rowid, daten):
    backup_erstellen()

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE kunstbilder
        SET "Künstler" = ?,
            "Titel" = ?,
            "Jahr" = ?,
            "Technik" = ?,
            "Maße" = ?,
            "Standort" = ?,
            "Rechte" = ?,
            "Beschreibung" = ?,
            "Schlagworte" = ?
        WHERE rowid = ?
        """,
        (
            daten["Künstler"],
            daten["Titel"],
            daten["Jahr"],
            daten["Technik"],
            daten["Maße"],
            daten["Standort"],
            daten["Rechte"],
            daten["Beschreibung"],
            daten["Schlagworte"],
            rowid,
        ),
    )

    conn.commit()
    conn.close()


def datensatz_loeschen(rowid, dateiname, bildpfad):
    backup_erstellen()

    echter_bildpfad = IMAGE_DIR / str(dateiname)

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM kunstbilder
        WHERE rowid = ?
           OR "Dateiname" = ?
           OR "Bildpfad" = ?
        """,
        (rowid, str(dateiname), str(bildpfad)),
    )

    conn.commit()
    conn.close()

    if echter_bildpfad.exists():
        echter_bildpfad.unlink()


def bild_laden(bildpfad):
    bild = Image.open(bildpfad)
    bild = ImageOps.exif_transpose(bild)
    return bild


def vorschaubild_erzeugen(bild, ziel_breite=260, ziel_hoehe=260):
    bild = bild.copy()
    bild.thumbnail((ziel_breite, ziel_hoehe))

    hintergrund = Image.new("RGB", (ziel_breite, ziel_hoehe), "white")

    x = (ziel_breite - bild.width) // 2
    y = (ziel_hoehe - bild.height) // 2

    if bild.mode in ("RGBA", "LA"):
        hintergrund.paste(bild, (x, y), bild)
    else:
        hintergrund.paste(bild, (x, y))

    return hintergrund


def kurzer_titel(text, max_laenge=18):
    text = str(text)

    if len(text) > max_laenge:
        return text[:max_laenge] + "..."

    return text


def bild_als_base64_data_url(bildpfad):
    suffix = bildpfad.suffix.lower()

    if suffix in [".jpg", ".jpeg"]:
        mime_type = "image/jpeg"
    elif suffix == ".png":
        mime_type = "image/png"
    elif suffix == ".webp":
        mime_type = "image/webp"
    else:
        bild = bild_laden(bildpfad)
        temp_buffer = BytesIO()
        bild.save(temp_buffer, format="JPEG")
        encoded = base64.b64encode(temp_buffer.getvalue()).decode("utf-8")
        return f"data:image/jpeg;base64,{encoded}"

    with open(bildpfad, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def ki_bildanalyse(bildpfad):
    api_key = st.secrets.get("OPENAI_API_KEY", "")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY fehlt in den Streamlit-Secrets.")

    client = OpenAI(api_key=api_key)

    data_url = bild_als_base64_data_url(bildpfad)

    prompt = """
Analysiere das Kunstbild für ein deutschsprachiges Kunstarchiv.

Gib ausschließlich gültiges JSON zurück, ohne Markdown, ohne Erklärung.

Schema:
{
  "beschreibung": "Ein sachlicher, kunsthistorisch brauchbarer Beschreibungstext mit 3 bis 5 Sätzen.",
  "schlagworte": "8 bis 12 Schlagworte, kommasepariert",
  "technik_stil": "Vorsichtige Einschätzung zu Technik, Stil, Gattung oder Bildtyp. Keine Gewissheiten behaupten, wenn sie nicht sichtbar sind."
}

Wichtig:
- Keine erfundenen Künstlernamen.
- Keine erfundenen Datierungen.
- Bei Unsicherheit Formulierungen wie „wirkt“, „erinnert an“, „möglicherweise“ verwenden.
- Beschreibe nur, was visuell plausibel erkennbar ist.
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

    kuenstler_neu = st.text_input("Künstler")
    titel_neu = st.text_input("Titel")
    jahr_neu = st.text_input("Jahr")
    technik_neu = st.text_input("Technik")
    masse_neu = st.text_input("Maße")
    standort_neu = st.text_input("Standort")
    rechte_neu = st.text_input("Rechte")
    beschreibung_neu = st.text_area("Beschreibung")
    schlagworte_neu = st.text_input("Schlagworte")

    if uploaded_files:
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
            backup_erstellen()
            gespeichert = 0

            for uploaded_file in uploaded_files:
                original_name = uploaded_file.name
                zielpfad = IMAGE_DIR / original_name

                counter = 1

                while zielpfad.exists():
                    stem = Path(original_name).stem
                    suffix = Path(original_name).suffix
                    zielpfad = IMAGE_DIR / f"{stem}_{counter}{suffix}"
                    counter += 1

                with open(zielpfad, "wb") as f:
                    shutil.copyfileobj(uploaded_file, f)

                daten = {
                    "Dateiname": zielpfad.name,
                    "Künstler": kuenstler_neu,
                    "Titel": titel_neu if titel_neu else zielpfad.stem,
                    "Jahr": jahr_neu,
                    "Technik": technik_neu,
                    "Maße": masse_neu,
                    "Standort": standort_neu,
                    "Rechte": rechte_neu,
                    "Beschreibung": beschreibung_neu,
                    "Schlagworte": schlagworte_neu,
                    "Bildpfad": str(zielpfad),
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

    kuenstler_liste = ["Alle"] + sorted(
        df["Künstler"].astype(str).unique().tolist()
    )

    kuenstler_filter = st.sidebar.selectbox(
        "Künstler",
        kuenstler_liste,
    )

    sortierung = st.sidebar.selectbox(
        "Sortieren nach",
        ["Titel", "Künstler", "Jahr", "Technik"],
    )

    gefiltert = df.copy()

    if suchbegriff:
        suchbegriff = suchbegriff.lower()

        gefiltert = gefiltert[
            gefiltert.astype(str)
            .apply(
                lambda row: row.str.lower().str.contains(suchbegriff).any(),
                axis=1,
            )
        ]

    if kuenstler_filter != "Alle":
        gefiltert = gefiltert[
            gefiltert["Künstler"].astype(str) == kuenstler_filter
        ]

    if sortierung in gefiltert.columns:
        gefiltert = gefiltert.sort_values(
            by=sortierung,
            ascending=True,
        )

    gefiltert = gefiltert.reset_index(drop=True)

    st.write(f"**{len(gefiltert)} Einträge gefunden**")

    export_excel = excel_export_erzeugen(gefiltert)

    export_csv = gefiltert.drop(
        columns=["rowid"],
        errors="ignore",
    ).to_csv(index=False).encode("utf-8-sig")

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
                bildpfad = IMAGE_DIR / str(row["Dateiname"])

                with spalten[i]:
                    with st.container(border=True):
                        if bildpfad.exists():
                            bild = bild_laden(bildpfad)
                            vorschau = vorschaubild_erzeugen(bild)

                            st.image(vorschau, width=260)

                            if st.button(
                                "Groß anzeigen",
                                key=f"gross_{row['rowid']}",
                            ):
                                st.session_state["ausgewaehlte_rowid"] = int(row["rowid"])
                                st.session_state["ansicht"] = "Detailansicht"
                                st.rerun()

                            with open(bildpfad, "rb") as file:
                                st.download_button(
                                    label="Bild herunterladen",
                                    data=file,
                                    file_name=bildpfad.name,
                                    mime="application/octet-stream",
                                    key=f"download_{row['rowid']}",
                                )
                        else:
                            st.warning("Bild nicht gefunden")

                        st.markdown(f"### {kurzer_titel(row.get('Titel', ''))}")
                        st.write(f"**Künstler:** {row.get('Künstler', '')}")
                        st.write(f"**Jahr:** {row.get('Jahr', '')}")

    else:
        auswahl_liste = [
            f"{row.get('Künstler', '')} – {row.get('Titel', '')} [{row.get('rowid', '')}]"
            for _, row in gefiltert.iterrows()
        ]

        if len(auswahl_liste) == 0:
            st.info("Keine Einträge gefunden.")
        else:
            vorauswahl_index = 0

            if st.session_state["ausgewaehlte_rowid"] is not None:
                for idx, row_check in gefiltert.iterrows():
                    if int(row_check["rowid"]) == int(st.session_state["ausgewaehlte_rowid"]):
                        vorauswahl_index = idx
                        break

            auswahl = st.selectbox(
                "Werk auswählen",
                auswahl_liste,
                index=vorauswahl_index,
            )

            index = auswahl_liste.index(auswahl)

            row = gefiltert.iloc[index]
            rowid = int(row["rowid"])

            st.session_state["ausgewaehlte_rowid"] = rowid

            bildpfad = IMAGE_DIR / str(row["Dateiname"])

            if st.button("Zurück zur Galerie"):
                st.session_state["ansicht"] = "Galerieansicht"
                st.rerun()

            col1, col2 = st.columns([1.4, 1])

            with col1:
                if bildpfad.exists():
                    bild = bild_laden(bildpfad)

                    st.image(
                        bild,
                        use_container_width=True,
                    )

                    with open(bildpfad, "rb") as file:
                        st.download_button(
                            label="Bild herunterladen",
                            data=file,
                            file_name=bildpfad.name,
                            mime="application/octet-stream",
                            key=f"detail_download_{rowid}",
                        )
                else:
                    st.warning(f"Bild nicht gefunden: {bildpfad}")

            with col2:
                st.header(str(row.get("Titel", "")))

                st.write(f"**Künstler:** {row.get('Künstler', '')}")
                st.write(f"**Jahr:** {row.get('Jahr', '')}")
                st.write(f"**Technik:** {row.get('Technik', '')}")
                st.write(f"**Maße:** {row.get('Maße', '')}")
                st.write(f"**Standort:** {row.get('Standort', '')}")
                st.write(f"**Rechte:** {row.get('Rechte', '')}")
                st.write(f"**Beschreibung:** {row.get('Beschreibung', '')}")
                st.write(f"**Schlagworte:** {row.get('Schlagworte', '')}")
                st.write(f"**Dateiname:** {row.get('Dateiname', '')}")

                st.divider()

                with st.expander("KI-Bildanalyse"):
                    st.write("Erzeugt eine Beschreibung, Schlagworte und eine vorsichtige Stil-/Technikeinschätzung.")

                    if st.button("KI-Beschreibung erzeugen", key=f"ki_{rowid}"):
                        if bildpfad.exists():
                            with st.spinner("KI analysiert das Bild..."):
                                try:
                                    analyse = ki_bildanalyse(bildpfad)

                                    st.session_state[f"ki_beschreibung_{rowid}"] = analyse.get("beschreibung", "")
                                    st.session_state[f"ki_schlagworte_{rowid}"] = analyse.get("schlagworte", "")
                                    st.session_state[f"ki_technik_{rowid}"] = analyse.get("technik_stil", "")

                                except Exception as e:
                                    st.error(f"Fehler bei der KI-Analyse: {e}")
                        else:
                            st.error("Bilddatei nicht gefunden.")

                    if st.session_state.get(f"ki_beschreibung_{rowid}"):
                        st.subheader("KI-Vorschlag")

                        st.write("**Beschreibung:**")
                        st.write(st.session_state[f"ki_beschreibung_{rowid}"])

                        st.write("**Schlagworte:**")
                        st.write(st.session_state[f"ki_schlagworte_{rowid}"])

                        st.write("**Technik/Stil:**")
                        st.write(st.session_state[f"ki_technik_{rowid}"])

                        if st.button("KI-Vorschlag in Datensatz übernehmen", key=f"ki_uebernehmen_{rowid}"):
                            neue_daten = {
                                "Künstler": str(row.get("Künstler", "")),
                                "Titel": str(row.get("Titel", "")),
                                "Jahr": str(row.get("Jahr", "")),
                                "Technik": st.session_state[f"ki_technik_{rowid}"],
                                "Maße": str(row.get("Maße", "")),
                                "Standort": str(row.get("Standort", "")),
                                "Rechte": str(row.get("Rechte", "")),
                                "Beschreibung": st.session_state[f"ki_beschreibung_{rowid}"],
                                "Schlagworte": st.session_state[f"ki_schlagworte_{rowid}"],
                            }

                            datensatz_aktualisieren(rowid, neue_daten)

                            st.success("KI-Vorschlag wurde übernommen.")
                            st.rerun()

                st.divider()

                with st.expander("Datensatz bearbeiten"):
                    with st.form(key=f"bearbeiten_form_{rowid}"):
                        bearb_kuenstler = st.text_input(
                            "Künstler",
                            value=str(row.get("Künstler", "")),
                        )

                        bearb_titel = st.text_input(
                            "Titel",
                            value=str(row.get("Titel", "")),
                        )

                        bearb_jahr = st.text_input(
                            "Jahr",
                            value=str(row.get("Jahr", "")),
                        )

                        bearb_technik = st.text_input(
                            "Technik",
                            value=str(row.get("Technik", "")),
                        )

                        bearb_masse = st.text_input(
                            "Maße",
                            value=str(row.get("Maße", "")),
                        )

                        bearb_standort = st.text_input(
                            "Standort",
                            value=str(row.get("Standort", "")),
                        )

                        bearb_rechte = st.text_input(
                            "Rechte",
                            value=str(row.get("Rechte", "")),
                        )

                        bearb_beschreibung = st.text_area(
                            "Beschreibung",
                            value=str(row.get("Beschreibung", "")),
                        )

                        bearb_schlagworte = st.text_input(
                            "Schlagworte",
                            value=str(row.get("Schlagworte", "")),
                        )

                        speichern = st.form_submit_button("Änderungen speichern")

                    if speichern:
                        neue_daten = {
                            "Künstler": bearb_kuenstler,
                            "Titel": bearb_titel,
                            "Jahr": bearb_jahr,
                            "Technik": bearb_technik,
                            "Maße": bearb_masse,
                            "Standort": bearb_standort,
                            "Rechte": bearb_rechte,
                            "Beschreibung": bearb_beschreibung,
                            "Schlagworte": bearb_schlagworte,
                        }

                        datensatz_aktualisieren(rowid, neue_daten)

                        st.success("Änderungen wurden gespeichert.")
                        st.rerun()

                st.divider()

                loeschen_bestaetigen = st.checkbox(
                    "Ich möchte diesen Datensatz wirklich löschen.",
                    key=f"loeschen_check_{rowid}",
                )

                if st.button(
                    "Datensatz löschen",
                    type="primary",
                    key=f"loeschen_{rowid}",
                ):
                    if loeschen_bestaetigen:
                        datensatz_loeschen(
                            rowid,
                            row["Dateiname"],
                            row["Bildpfad"],
                        )

                        st.success("Datensatz wurde gelöscht.")
                        st.rerun()
                    else:
                        st.error("Bitte zuerst die Löschung bestätigen.")