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


# =========================================================
# SETUP
# =========================================================

st.set_page_config(
    page_title="Kunstbild-Datenbank",
    layout="wide",
)

lade_css()


# =========================================================
# HILFSFUNKTIONEN
# =========================================================

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


def kurzer_titel(text, max_laenge=36):

    text = str(text)

    if len(text) > max_laenge:
        return text[:max_laenge] + "..."

    return text


def login_pruefen():

    st.title("Kunstbild-Datenbank")

    eingabe = st.text_input(
        "Passwort",
        type="password",
    )

    if eingabe == PASSWORT:

        st.session_state["eingeloggt"] = True
        st.rerun()

    elif eingabe:

        st.error("Falsches Passwort")


# =========================================================
# SESSION STATE
# =========================================================

if "eingeloggt" not in st.session_state:
    st.session_state["eingeloggt"] = False

if "seite" not in st.session_state:
    st.session_state["seite"] = "Archiv"

if "ansicht" not in st.session_state:
    st.session_state["ansicht"] = "Galerie"

if "ausgewaehlte_id" not in st.session_state:
    st.session_state["ausgewaehlte_id"] = None

if "ki_upload_analyse" not in st.session_state:
    st.session_state["ki_upload_analyse"] = {}


if not st.session_state["eingeloggt"]:

    login_pruefen()
    st.stop()


# =========================================================
# HEADER
# =========================================================

st.title("Kunstbild-Datenbank")

st.caption(
    "Recherche, Vorschau, Upload, Export und Verwaltung deiner Kunstbilder"
)


# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("Navigation")

    seite = st.radio(
        "Bereich",
        [
            "Archiv",
            "Upload",
        ],
    )

    st.session_state["seite"] = seite

    st.divider()

    if st.button("Abmelden"):

        st.session_state["eingeloggt"] = False
        st.rerun()


# =========================================================
# UPLOAD
# =========================================================

if seite == "Upload":

    st.header("Neue Bilder hochladen")

    uploaded_files = st.file_uploader(
        "Bilddateien auswählen",
        type=["jpg", "jpeg", "png", "webp"],
        accept_multiple_files=True,
    )

    kuenstler = st.text_input("Künstler")
    titel = st.text_input("Titel")
    jahr = st.text_input("Jahr")

    stile = st.multiselect(
        "Stil / Epoche",
        STIL_OPTIONEN,
    )

    techniken = st.multiselect(
        "Techniken",
        TECHNIK_OPTIONEN,
    )

    gattungen = st.multiselect(
        "Gattung / Motiv",
        GATTUNG_OPTIONEN,
    )

    technik = st.text_input("Technik")
    masse = st.text_input("Maße")
    standort = st.text_input("Standort")
    rechte = st.text_input("Rechte")

    beschreibung = st.text_area("Beschreibung")
    schlagworte = st.text_input("Schlagworte")

    if uploaded_files:

        spalten = st.columns(4)

        for index, bild in enumerate(uploaded_files):

            with spalten[index % 4]:

                st.image(
                    bild,
                    width=150,
                )

                st.caption(bild.name)

    if st.button("Bilder speichern"):

        if not uploaded_files:

            st.error("Keine Bilder ausgewählt")

        else:

            gespeichert = 0

            for bild in uploaded_files:

                (
                    dateiname,
                    bild_url,
                    thumbnail_url,
                ) = bild_nach_supabase(bild)

                daten = {
                    "dateiname": dateiname,
                    "kuenstler": kuenstler,
                    "titel": titel if titel else bild.name,
                    "jahr": jahr,
                    "technik": technik,
                    "masse": masse,
                    "standort": standort,
                    "rechte": rechte,
                    "beschreibung": beschreibung,
                    "schlagworte": schlagworte,
                    "bildpfad": bild_url,
                    "thumbnailpfad": thumbnail_url,
                    "stile": liste_zu_text(stile),
                    "techniken": liste_zu_text(techniken),
                    "gattungen": liste_zu_text(gattungen),
                }

                datensatz_speichern(daten)

                gespeichert += 1

            st.success(
                f"{gespeichert} Bilder gespeichert"
            )

            st.rerun()


# =========================================================
# ARCHIV
# =========================================================

else:

    df = daten_laden()

    # =====================================================
    # FILTER
    # =====================================================

    st.sidebar.header("Filter")

    suche = st.sidebar.text_input(
        "Freie Suche"
    )

    kuenstler_liste = ["Alle"] + sorted(
        df["kuenstler"].astype(str).unique().tolist()
    )

    kuenstler_filter = st.sidebar.selectbox(
        "Künstler",
        kuenstler_liste,
    )

    gefiltert = df.copy()

    if suche:

        suche = suche.lower()

        gefiltert = gefiltert[
            gefiltert.astype(str)
            .apply(
                lambda row: row.str.lower().str.contains(suche).any(),
                axis=1,
            )
        ]

    if kuenstler_filter != "Alle":

        gefiltert = gefiltert[
            gefiltert["kuenstler"].astype(str)
            == kuenstler_filter
        ]

    gefiltert = gefiltert.reset_index(drop=True)

    # =====================================================
    # TOOLS
    # =====================================================

    st.write(f"**{len(gefiltert)} Einträge gefunden**")

    tool1, tool2 = st.columns([1, 1])

    with tool1:

        export_excel = excel_export_erzeugen(
            gefiltert
        )

        st.download_button(
            "Trefferliste als Excel herunterladen",
            data=export_excel,
            file_name="kunstbilder.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    with tool2:

        if st.button("PDF-Katalog erzeugen"):

            pdf = pdf_katalog_erzeugen(
                gefiltert
            )

            st.download_button(
                "PDF herunterladen",
                data=pdf,
                file_name="kunstbilder.pdf",
                mime="application/pdf",
            )

    ansicht = st.radio(
        "Ansicht",
        [
            "Galerie",
            "Details",
        ],
        horizontal=True,
    )

    # =====================================================
    # GALERIE
    # =====================================================

    if ansicht == "Galerie":

        kompakt = st.toggle(
            "Kompakte Galerie",
            value=True,
        )

        spaltenzahl = 2 if kompakt else 3

        for start in range(0, len(gefiltert), spaltenzahl):

            spalten = st.columns(spaltenzahl)

            for i in range(spaltenzahl):

                if start + i >= len(gefiltert):
                    continue

                row = gefiltert.iloc[start + i]

                bild_url = (
                    row["thumbnailpfad"]
                    if row["thumbnailpfad"]
                    else row["bildpfad"]
                )

                with spalten[i]:

                    with st.container(border=True):

                        st.markdown(
                            bild_html(bild_url),
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f"""
                            <div class="kunst-title">
                                {kurzer_titel(row.get("titel", ""))}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f"""
                            <div class="kunst-meta-kompakt">
                                <strong>{row.get("kuenstler", "")}</strong><br>
                                {row.get("jahr", "")}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

                        button1, button2 = st.columns(2)

                        with button1:

                            if st.button(
                                "Öffnen",
                                key=f"open_{row['id']}",
                                use_container_width=True,
                            ):

                                st.session_state["ausgewaehlte_id"] = int(row["id"])
                                st.session_state["ansicht"] = "Details"

                                st.rerun()

                        with button2:

                            try:

                                bild_download = requests.get(
                                    row["bildpfad"],
                                    timeout=20,
                                ).content

                                st.download_button(
                                    "Download",
                                    data=bild_download,
                                    file_name=str(row["dateiname"]),
                                    mime="application/octet-stream",
                                    key=f"download_{row['id']}",
                                    use_container_width=True,
                                )

                            except Exception:

                                st.info("Download nicht möglich")

    # =====================================================
    # DETAILS
    # =====================================================

    else:

        if len(gefiltert) == 0:

            st.info("Keine Werke gefunden")

        else:

            auswahl_liste = [
                f"{row.get('kuenstler', '')} – {row.get('titel', '')}"
                for _, row in gefiltert.iterrows()
            ]

            index = st.selectbox(
                "Werk auswählen",
                range(len(auswahl_liste)),
                format_func=lambda x: auswahl_liste[x],
            )

            row = gefiltert.iloc[index]

            col1, col2 = st.columns([1.5, 1])

            with col1:

                st.image(
                    row["bildpfad"],
                    use_container_width=True,
                )

            with col2:

                st.header(
                    str(row.get("titel", ""))
                )

                st.write(
                    f"**Künstler:** {row.get('kuenstler', '')}"
                )

                st.write(
                    f"**Jahr:** {row.get('jahr', '')}"
                )

                st.write(
                    f"**Technik:** {row.get('technik', '')}"
                )

                st.write(
                    f"**Maße:** {row.get('masse', '')}"
                )

                st.write(
                    f"**Standort:** {row.get('standort', '')}"
                )

                st.write(
                    f"**Rechte:** {row.get('rechte', '')}"
                )

                st.write(
                    f"**Beschreibung:** {row.get('beschreibung', '')}"
                )

                st.write(
                    f"**Schlagworte:** {row.get('schlagworte', '')}"
                )

                st.divider()

                with st.expander("Datensatz bearbeiten"):

                    with st.form(
                        key=f"edit_{row['id']}"
                    ):

                        neu_kuenstler = st.text_input(
                            "Künstler",
                            value=str(row.get("kuenstler", "")),
                        )

                        neu_titel = st.text_input(
                            "Titel",
                            value=str(row.get("titel", "")),
                        )

                        neu_jahr = st.text_input(
                            "Jahr",
                            value=str(row.get("jahr", "")),
                        )

                        neu_technik = st.text_input(
                            "Technik",
                            value=str(row.get("technik", "")),
                        )

                        neu_beschreibung = st.text_area(
                            "Beschreibung",
                            value=str(row.get("beschreibung", "")),
                        )

                        speichern = st.form_submit_button(
                            "Änderungen speichern"
                        )

                    if speichern:

                        neue_daten = {
                            "kuenstler": neu_kuenstler,
                            "titel": neu_titel,
                            "jahr": neu_jahr,
                            "technik": neu_technik,
                            "beschreibung": neu_beschreibung,
                        }

                        datensatz_aktualisieren(
                            row["id"],
                            neue_daten,
                        )

                        st.success(
                            "Datensatz gespeichert"
                        )

                        st.rerun()

                st.divider()

                if st.button(
                    "Datensatz löschen",
                    type="primary",
                ):

                    datensatz_loeschen(
                        row["id"],
                        row["dateiname"],
                        row.get("thumbnailpfad", ""),
                    )

                    st.success(
                        "Datensatz gelöscht"
                    )

                    st.rerun()