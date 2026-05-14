import requests
import streamlit as st
from html import escape

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
)

from pdf_export import pdf_katalog_erzeugen
from ai_tools import ki_upload_analyse


st.set_page_config(
    page_title="Kunstbild-Datenbank",
    layout="wide",
)

lade_css()


def text_zu_liste(text):
    if not text:
        return []
    return [x.strip() for x in str(text).split(",") if x.strip()]


def liste_zu_text(liste):
    return ", ".join(liste)


def kurzer_titel(text, max_laenge=38):
    text = str(text)
    if len(text) > max_laenge:
        return text[:max_laenge] + "..."
    return text


def clear_query_params():
    try:
        st.query_params.clear()
    except Exception:
        pass


def galerie_grid_html(df):
    cards = []

    for _, row in df.iterrows():
        datensatz_id = row.get("id", "")
        bild_url = row.get("thumbnailpfad", "") or row.get("bildpfad", "")
        titel = kurzer_titel(row.get("titel", ""))
        kuenstler = row.get("kuenstler", "")
        jahr = row.get("jahr", "")

        cards.append(
            f"""
            <a class="kunst-grid-card" href="?selected_id={datensatz_id}">
                <div class="kunst-grid-image">
                    <img src="{escape(str(bild_url), quote=True)}" alt="">
                </div>
                <div class="kunst-grid-title">{escape(str(titel))}</div>
                <div class="kunst-grid-meta">
                    {escape(str(kuenstler))}<br>
                    {escape(str(jahr))}
                </div>
            </a>
            """
        )

    html = f"""
    <style>
        .kunst-grid {{
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 1rem;
            margin-top: 1.2rem;
        }}

        .kunst-grid-card {{
            display: block;
            text-decoration: none !important;
            background: #111827;
            border: 1px solid #374151;
            border-radius: 14px;
            padding: 0.75rem;
            color: #f5f5f5 !important;
            transition: transform 0.12s ease, border-color 0.12s ease;
        }}

        .kunst-grid-card:hover {{
            transform: translateY(-2px);
            border-color: #6b7280;
        }}

        .kunst-grid-image {{
            width: 100%;
            aspect-ratio: 1 / 1;
            background: #141820;
            border-radius: 12px;
            overflow: hidden;
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .kunst-grid-image img {{
            max-width: 100%;
            max-height: 100%;
            object-fit: contain;
        }}

        .kunst-grid-title {{
            margin-top: 0.65rem;
            font-weight: 700;
            font-size: 0.96rem;
            line-height: 1.25;
            color: #ffffff;
        }}

        .kunst-grid-meta {{
            margin-top: 0.35rem;
            font-size: 0.82rem;
            line-height: 1.35;
            color: #d1d5db;
        }}

        @media (max-width: 900px) {{
            .kunst-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.75rem;
            }}

            .kunst-grid-card {{
                padding: 0.6rem;
                border-radius: 12px;
            }}

            .kunst-grid-title {{
                font-size: 0.86rem;
            }}

            .kunst-grid-meta {{
                font-size: 0.76rem;
            }}
        }}

        @media (max-width: 420px) {{
            .kunst-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.65rem;
            }}

            .kunst-grid-card {{
                padding: 0.5rem;
            }}
        }}
    </style>

    <div class="kunst-grid">
        {''.join(cards)}
    </div>
    """

    return html


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


if "selected_id" in st.query_params:
    try:
        st.session_state["ausgewaehlte_id"] = int(st.query_params["selected_id"])
        st.session_state["ansicht"] = "Detailansicht"
        st.session_state["seite"] = "Archiv durchsuchen"
    except Exception:
        pass


if not st.session_state["eingeloggt"]:
    login_pruefen()
    st.stop()


st.title("Kunstbild-Datenbank")
st.caption("Recherche, Vorschau, Upload, Export und Verwaltung deiner Kunstbilder")


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
        clear_query_params()
        st.rerun()

    uploaded_files = st.file_uploader(
        "Bilddateien auswählen",
        type=["jpg", "jpeg", "png", "webp", "tif", "tiff"],
        accept_multiple_files=True,
    )

    kuenstler_neu = st.text_input("Künstler")
    titel_neu = st.text_input("Titel")
    jahr_neu = st.text_input("Jahr")

    stile_neu = st.multiselect("Stil / Epoche", STIL_OPTIONEN)
    techniken_neu = st.multiselect("Techniken", TECHNIK_OPTIONEN)
    gattungen_neu = st.multiselect("Gattung / Motiv", GATTUNG_OPTIONEN)

    technik_neu = ""
    beschreibung_neu = ""
    schlagworte_neu = ""

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

        analyse = st.session_state.get("ki_upload_analyse", {})

        if analyse:
            technik_neu = analyse.get("technik", "")
            beschreibung_neu = analyse.get("beschreibung", "")
            schlagworte_neu = analyse.get("schlagworte", "")
            stile_neu = text_zu_liste(analyse.get("stile", ""))
            techniken_neu = text_zu_liste(analyse.get("techniken", ""))
            gattungen_neu = text_zu_liste(analyse.get("gattungen", ""))

    technik_neu = st.text_input("Technik", value=technik_neu)
    masse_neu = st.text_input("Maße")
    standort_neu = st.text_input("Standort")
    rechte_neu = st.text_input("Rechte")
    beschreibung_neu = st.text_area("Beschreibung", value=beschreibung_neu)
    schlagworte_neu = st.text_input("Schlagworte", value=schlagworte_neu)

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
                eindeutiger_name, public_url, thumbnail_url = bild_nach_supabase(
                    uploaded_file
                )

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
            clear_query_params()
            st.rerun()


else:

    df = daten_laden()

    st.sidebar.header("Filter")

    suchbegriff = st.sidebar.text_input("Freie Suche")

    kuenstler_liste = ["Alle"] + sorted(
        df["kuenstler"].astype(str).unique().tolist()
    )

    kuenstler_filter = st.sidebar.selectbox("Künstler", kuenstler_liste)
    stil_filter = st.sidebar.multiselect("Stil / Epoche", STIL_OPTIONEN)
    technik_filter = st.sidebar.multiselect("Techniken", TECHNIK_OPTIONEN)
    gattung_filter = st.sidebar.multiselect("Gattung / Motiv", GATTUNG_OPTIONEN)

    gefiltert = df.copy()

    if suchbegriff:
        suchbegriff = suchbegriff.lower()
        gefiltert = gefiltert[
            gefiltert.astype(str).apply(
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
        if st.button("PDF-Katalog erzeugen"):
            with st.spinner("PDF wird erstellt ..."):
                pdf_katalog = pdf_katalog_erzeugen(gefiltert)

                st.download_button(
                    label="PDF-Katalog herunterladen",
                    data=pdf_katalog,
                    file_name="kunstbilder_katalog.pdf",
                    mime="application/pdf",
                )

    ansicht = st.radio(
        "Ansicht",
        ["Galerieansicht", "Detailansicht"],
        horizontal=True,
        index=0 if st.session_state["ansicht"] == "Galerieansicht" else 1,
    )

    st.session_state["ansicht"] = ansicht

    if ansicht == "Galerieansicht":

        st.html(
    galerie_grid_html(gefiltert)
)

    else:

        if len(gefiltert) == 0:
            st.info("Keine Einträge gefunden.")

        else:
            auswahl_liste = [
                f"{row.get('kuenstler', '')} – {row.get('titel', '')}"
                for _, row in gefiltert.iterrows()
            ]

            vorauswahl_index = 0

            if st.session_state["ausgewaehlte_id"] is not None:
                for idx, row_check in gefiltert.iterrows():
                    if int(row_check["id"]) == int(
                        st.session_state["ausgewaehlte_id"]
                    ):
                        vorauswahl_index = idx
                        break

            auswahl = st.selectbox(
                "Werk auswählen",
                auswahl_liste,
                index=vorauswahl_index,
            )

            index = auswahl_liste.index(auswahl)
            row = gefiltert.iloc[index]

            if st.button("← Zurück zur Galerie"):
                st.session_state["ansicht"] = "Galerieansicht"
                st.session_state["ausgewaehlte_id"] = None
                clear_query_params()
                st.rerun()

            col1, col2 = st.columns([1.4, 1])

            with col1:
                st.image(row["bildpfad"], use_container_width=True)

                try:
                    bild_download = requests.get(
                        row["bildpfad"],
                        timeout=20,
                    ).content

                    st.download_button(
                        label="Bild herunterladen",
                        data=bild_download,
                        file_name=str(row["dateiname"]),
                        mime="application/octet-stream",
                        key=f"detail_download_{row['id']}",
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

                with st.expander("Datensatz bearbeiten"):
                    with st.form(key=f"bearbeiten_form_{row['id']}"):

                        bearb_kuenstler = st.text_input(
                            "Künstler",
                            value=str(row.get("kuenstler", "")),
                        )

                        bearb_titel = st.text_input(
                            "Titel",
                            value=str(row.get("titel", "")),
                        )

                        bearb_jahr = st.text_input(
                            "Jahr",
                            value=str(row.get("jahr", "")),
                        )

                        bearb_technik = st.text_input(
                            "Technik",
                            value=str(row.get("technik", "")),
                        )

                        bearb_masse = st.text_input(
                            "Maße",
                            value=str(row.get("masse", "")),
                        )

                        bearb_standort = st.text_input(
                            "Standort",
                            value=str(row.get("standort", "")),
                        )

                        bearb_rechte = st.text_input(
                            "Rechte",
                            value=str(row.get("rechte", "")),
                        )

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

                        bearb_beschreibung = st.text_area(
                            "Beschreibung",
                            value=str(row.get("beschreibung", "")),
                        )

                        bearb_schlagworte = st.text_input(
                            "Schlagworte",
                            value=str(row.get("schlagworte", "")),
                        )

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

                        datensatz_aktualisieren(row["id"], neue_daten)

                        st.success("Änderungen wurden gespeichert.")
                        st.rerun()

                st.divider()

                with st.popover("🗑 Datensatz löschen"):
                    st.warning("Diesen Datensatz wirklich endgültig löschen?")

                    if st.button(
                        "Ja, endgültig löschen",
                        key=f"confirm_delete_detail_{row['id']}",
                    ):
                        datensatz_loeschen(
                            row["id"],
                            row["dateiname"],
                            row.get("thumbnailpfad", ""),
                        )

                        st.success("Datensatz wurde gelöscht.")
                        st.session_state["ansicht"] = "Galerieansicht"
                        st.session_state["ausgewaehlte_id"] = None
                        clear_query_params()
                        st.rerun()