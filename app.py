import requests
import streamlit as st

from constants import (
    PASSWORT,
    STIL_OPTIONEN,
    TECHNIK_OPTIONEN,
    GATTUNG_OPTIONEN,
)

from styles import lade_css

from database import (
    daten_laden,
    datensatz_speichern,
    datensatz_aktualisieren,
    datensatz_loeschen,
    excel_export_erzeugen,
)

from storage import (
    bild_nach_supabase,
    bild_html,
)

from pdf_export import pdf_katalog_erzeugen

from ai_tools import ki_upload_analyse


st.set_page_config(
    page_title="Kunstbild-Datenbank",
    layout="wide"
)

lade_css()


def text_zu_liste(text):
    if not text:
        return []

    return [
        x.strip()
        for x in str(text).split(",")
        if x.strip()
    ]


def liste_zu_text(liste):
    return ", ".join(liste)


def kurzer_titel(text, max_laenge=32):
    text = str(text)

    if len(text) > max_laenge:
        return text[:max_laenge] + "..."

    return text


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
st.caption("Recherche, Vorschau, Upload, Export und Verwaltung deiner Kunstbilder")


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

    st.header("Neue Bilder hinzufügen")

    if st.button("← Zurück zum Archiv"):
        st.session_state["seite"] = "Archiv durchsuchen"
        st.session_state["ansicht"] = "Galerieansicht"
        st.rerun()

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

    kuenstler_neu = st.text_input("Künstler")
    titel_neu = st.text_input("Titel")
    jahr_neu = st.text_input("Jahr")

    stile_neu = st.multiselect(
        "Stil / Epoche",
        STIL_OPTIONEN,
    )

    techniken_neu = st.multiselect(
        "Techniken",
        TECHNIK_OPTIONEN,
    )

    gattungen_neu = st.multiselect(
        "Gattung / Motiv",
        GATTUNG_OPTIONEN,
    )

    technik_neu = st.text_input("Technik")
    masse_neu = st.text_input("Maße")
    standort_neu = st.text_input("Standort")
    rechte_neu = st.text_input("Rechte")

    beschreibung_neu = st.text_area("Beschreibung")
    schlagworte_neu = st.text_input("Schlagworte")

    if uploaded_files:

        erste_datei = uploaded_files[0]

        if st.button("KI-Analyse durchführen"):

            with st.spinner("KI analysiert Bild ..."):

                analyse = ki_upload_analyse(
                    erste_datei,
                    kuenstler_neu,
                    titel_neu,
                    jahr_neu,
                )

                st.session_state["ki_upload_analyse"] = analyse

                st.rerun()

        analyse = st.session_state.get(
            "ki_upload_analyse",
            {}
        )

        if analyse:

            if not technik_neu:
                technik_neu = analyse.get("technik", "")

            if not beschreibung_neu:
                beschreibung_neu = analyse.get("beschreibung", "")

            if not schlagworte_neu:
                schlagworte_neu = analyse.get("schlagworte", "")

            if not stile_neu:
                stile_neu = text_zu_liste(analyse.get("stile", ""))

            if not techniken_neu:
                techniken_neu = text_zu_liste(analyse.get("techniken", ""))

            if not gattungen_neu:
                gattungen_neu = text_zu_liste(analyse.get("gattungen", ""))

    technik_neu = st.text_input(
        "Technik",
        value=technik_neu,
    )

    beschreibung_neu = st.text_area(
        "Beschreibung",
        value=beschreibung_neu,
    )

    schlagworte_neu = st.text_input(
        "Schlagworte",
        value=schlagworte_neu,
    )

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
            gespeichert = 0

            for uploaded_file in uploaded_files:

                (
                    eindeutiger_name,
                    public_url,
                    thumbnail_url,
                ) = bild_nach_supabase(uploaded_file)

                daten = {
                    "dateiname": eindeutiger_name,
                    "kuenstler": kuenstler_neu,
                    "titel": titel_neu if titel_neu else uploaded_file.name,
                    "jahr": jahr_neu,
                    "technik": technik_neu,
                    "masse": masse_neu,
                    "standort": standort_neu,
                    "rechte": rechte_neu,
                    "beschreibung": beschreibung_neu,
                    "schlagworte": schlagworte_neu,
                    "bildpfad": public_url,
                    "thumbnailpfad": thumbnail_url,
                    "stile": liste_zu_text(stile_neu),
                    "techniken": liste_zu_text(techniken_neu),
                    "gattungen": liste_zu_text(gattungen_neu),
                }

                datensatz_speichern(daten)

                gespeichert += 1

            st.session_state["ki_upload_analyse"] = {}

            st.success(f"{gespeichert} Bilder gespeichert.")

            st.session_state["seite"] = "Archiv durchsuchen"
            st.session_state["ansicht"] = "Galerieansicht"

            st.rerun()


else:

    df = daten_laden()

    st.sidebar.header("Filter")

    suchbegriff = st.sidebar.text_input("Freie Suche")

    kuenstler_liste = ["Alle"] + sorted(
        df["kuenstler"].astype(str).unique().tolist()
    )

    kuenstler_filter = st.sidebar.selectbox(
        "Künstler",
        kuenstler_liste,
    )

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
            gefiltert["kuenstler"].astype(str) == kuenstler_filter
        ]

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

    gefiltert = gefiltert.reset_index(drop=True)

    st.write(f"**{len(gefiltert)} Einträge gefunden**")

    col_export1, col_export2 = st.columns([1, 1])

    with col_export1:

        export_excel = excel_export_erzeugen(gefiltert)

        st.download_button(
            label="Trefferliste als Excel herunterladen",
            data=export_excel,
            file_name="kunstbilder_export.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with col_export2:

        pdf_katalog = pdf_katalog_erzeugen(gefiltert)

        st.download_button(
            label="PDF-Katalog herunterladen",
            data=pdf_katalog,
            file_name="kunstbilder_katalog.pdf",
            mime="application/pdf",
        )

    st.success(
        "Projekt erfolgreich modularisiert."
    )