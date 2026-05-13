import streamlit as st
import pandas as pd
import sqlite3
import shutil
import base64
import json
import uuid
from pathlib import Path
from datetime import datetime
from io import BytesIO
from PIL import Image, ImageOps
from openai import OpenAI
from supabase import create_client

BASE_DIR = Path(__file__).parent
DB_FILE = BASE_DIR / "kunstbilder.db"
IMAGE_DIR = BASE_DIR / "Bilder"
BACKUP_DIR = BASE_DIR / "Backups"

PASSWORT = "kunstarchiv2026"

IMAGE_DIR.mkdir(exist_ok=True)
BACKUP_DIR.mkdir(exist_ok=True)

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

    df = pd.read_sql_query(
        "SELECT rowid, * FROM kunstbilder",
        conn
    )

    conn.close()

    return df.fillna("")


def excel_export_erzeugen(df):

    export_df = df.drop(columns=["rowid"], errors="ignore")

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        export_df.to_excel(
            writer,
            index=False,
            sheet_name="Kunstbilder"
        )

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

    conn = sqlite3.connect(DB_FILE)

    cursor = conn.cursor()

    cursor.execute(
        """
        DELETE FROM kunstbilder
        WHERE rowid = ?
        """,
        (rowid,),
    )

    conn.commit()

    conn.close()

    if str(bildpfad).startswith("http"):

        try:

            filename = bildpfad.split("/")[-1]

            supabase.storage.from_(SUPABASE_BUCKET).remove([filename])

        except:
            pass

    else:

        echter_bildpfad = IMAGE_DIR / str(dateiname)

        if echter_bildpfad.exists():

            echter_bildpfad.unlink()


def bild_laden(bildpfad):

    bild = Image.open(bildpfad)

    bild = ImageOps.exif_transpose(bild)

    return bild


def vorschaubild_erzeugen(bild, ziel_breite=260, ziel_hoehe=260):

    bild = bild.copy()

    bild.thumbnail((ziel_breite, ziel_hoehe))

    hintergrund = Image.new(
        "RGB",
        (ziel_breite, ziel_hoehe),
        "white"
    )

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

    suffix = str(bildpfad).lower()

    if suffix.endswith(".jpg") or suffix.endswith(".jpeg"):

        mime_type = "image/jpeg"

    elif suffix.endswith(".png"):

        mime_type = "image/png"

    elif suffix.endswith(".webp"):

        mime_type = "image/webp"

    else:

        mime_type = "image/jpeg"

    if str(bildpfad).startswith("http"):

        import requests

        response = requests.get(bildpfad)

        encoded = base64.b64encode(response.content).decode("utf-8")

    else:

        with open(bildpfad, "rb") as f:

            encoded = base64.b64encode(f.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def ki_bildanalyse(bildpfad):

    api_key = st.secrets.get("OPENAI_API_KEY", "")

    client = OpenAI(api_key=api_key)

    data_url = bild_als_base64_data_url(bildpfad)

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
                    {"type": "input_text", "text": prompt},
                    {"type": "input_image", "image_url": data_url},
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


def bild_nach_supabase(uploaded_file):

    suffix = Path(uploaded_file.name).suffix

    eindeutiger_name = f"{uuid.uuid4()}{suffix}"

    file_bytes = uploaded_file.getvalue()

    supabase.storage.from_(SUPABASE_BUCKET).upload(
        eindeutiger_name,
        file_bytes,
        {"content-type": uploaded_file.type}
    )

    public_url = supabase.storage.from_(
        SUPABASE_BUCKET
    ).get_public_url(eindeutiger_name)

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

                eindeutiger_name, public_url = bild_nach_supabase(
                    uploaded_file
                )

                daten = {
                    "Dateiname": eindeutiger_name,
                    "Künstler": kuenstler_neu,
                    "Titel": titel_neu if titel_neu else eindeutiger_name,
                    "Jahr": jahr_neu,
                    "Technik": technik_neu,
                    "Maße": masse_neu,
                    "Standort": standort_neu,
                    "Rechte": rechte_neu,
                    "Beschreibung": beschreibung_neu,
                    "Schlagworte": schlagworte_neu,
                    "Bildpfad": public_url,
                }

                datensatz_speichern(daten)

                gespeichert += 1

            st.session_state["seite"] = "Archiv durchsuchen"

            st.session_state["ansicht"] = "Galerieansicht"

            st.success(f"{gespeichert} Bilder gespeichert.")

            st.rerun()


else:

    st.success(
        "Supabase-Integration aktiv. Neue Bilder werden dauerhaft online gespeichert."
    )

    st.info(
        "Bestehende lokale Bilder funktionieren weiterhin parallel."
    )