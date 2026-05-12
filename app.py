import streamlit as st
import pandas as pd
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "kunstbilder.db"
IMAGE_DIR = BASE_DIR / "Bilder"
BACKUP_DIR = BASE_DIR / "Backups"

PASSWORT = "kunstarchiv2026"

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

if not st.session_state["eingeloggt"]:
    login_pruefen()
    st.stop()


st.title("Kunstbild-Datenbank")
st.caption("Recherche, Vorschau, Upload, Export und Verwaltung deiner Kunstbilder")

if st.sidebar.button("Abmelden"):
    st.session_state["eingeloggt"] = False
    st.rerun()


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
    backup_erstellen()

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


tab1, tab2 = st.tabs(["Archiv durchsuchen", "Neues Bild hinzufügen"])


with tab2:
    st.header("Neues Bild hinzufügen")

    uploaded_files = st.file_uploader(
    "Bilddateien auswählen",
    type=["jpg", "jpeg", "png", "webp", "tif", "tiff"],
    accept_multiple_files=True
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
        elif not titel_neu:
            st.error("Bitte mindestens einen Titel eingeben.")
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

    st.success(f"{gespeichert} Bilder gespeichert.")

    st.rerun()


with tab1:
    df = daten_laden()

    st.sidebar.header("Filter")

    suchbegriff = st.sidebar.text_input("Freie Suche")

    kuenstler_liste = ["Alle"] + sorted(df["Künstler"].astype(str).unique().tolist())
    kuenstler_filter = st.sidebar.selectbox("Künstler", kuenstler_liste)

    sortierung = st.sidebar.selectbox(
        "Sortieren nach",
        ["Titel", "Künstler", "Jahr", "Technik"],
    )

    gefiltert = df.copy()

    if suchbegriff:
        suchbegriff = suchbegriff.lower()
        gefiltert = gefiltert[
            gefiltert.astype(str)
            .apply(lambda row: row.str.lower().str.contains(suchbegriff).any(), axis=1)
        ]

    if kuenstler_filter != "Alle":
        gefiltert = gefiltert[
            gefiltert["Künstler"].astype(str) == kuenstler_filter
        ]

    if sortierung in gefiltert.columns:
        gefiltert = gefiltert.sort_values(by=sortierung, ascending=True)

    gefiltert = gefiltert.reset_index(drop=True)

    st.write(f"**{len(gefiltert)} Einträge gefunden**")

    export_excel = excel_export_erzeugen(gefiltert)
    export_csv = gefiltert.drop(columns=["rowid"], errors="ignore").to_csv(index=False).encode("utf-8-sig")

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
    )

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
            auswahl = st.selectbox("Werk auswählen", auswahl_liste)
            index = auswahl_liste.index(auswahl)
            row = gefiltert.iloc[index]
            rowid = int(row["rowid"])

            bildpfad = IMAGE_DIR / str(row["Dateiname"])

            col1, col2 = st.columns([1, 2])

            with col1:
                if bildpfad.exists():
                    bild = bild_laden(bildpfad)
                    st.image(bild, width=420)

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

                with st.expander("Datensatz bearbeiten"):
                    with st.form(key=f"bearbeiten_form_{rowid}"):
                        bearb_kuenstler = st.text_input("Künstler", value=str(row.get("Künstler", "")))
                        bearb_titel = st.text_input("Titel", value=str(row.get("Titel", "")))
                        bearb_jahr = st.text_input("Jahr", value=str(row.get("Jahr", "")))
                        bearb_technik = st.text_input("Technik", value=str(row.get("Technik", "")))
                        bearb_masse = st.text_input("Maße", value=str(row.get("Maße", "")))
                        bearb_standort = st.text_input("Standort", value=str(row.get("Standort", "")))
                        bearb_rechte = st.text_input("Rechte", value=str(row.get("Rechte", "")))
                        bearb_beschreibung = st.text_area("Beschreibung", value=str(row.get("Beschreibung", "")))
                        bearb_schlagworte = st.text_input("Schlagworte", value=str(row.get("Schlagworte", "")))

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

                if st.button("Datensatz löschen", type="primary", key=f"loeschen_{rowid}"):
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