import streamlit as st

from constants import (
    STIL_OPTIONEN,
    TECHNIK_OPTIONEN,
    GATTUNG_OPTIONEN,
)

from storage import bild_nach_supabase
from database import datensatz_speichern
from ai_tools import ki_upload_analyse
from activity import log_activity

from filter_utils import (
    text_zu_liste,
    liste_zu_text,
    filter_optionen,
)


def upload_view(user_email):
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

    kuenstler_neu = st.text_input("Künstler")
    titel_neu = st.text_input("Titel")
    jahr_neu = st.text_input("Jahr")

    if uploaded_files:
        if st.button("KI-Analyse durchführen"):
            with st.spinner("KI analysiert Bild ..."):
                analyse = ki_upload_analyse(
                    uploaded_files[0],
                    kuenstler_neu,
                    titel_neu,
                    jahr_neu,
                )

                st.session_state["ki_upload_analyse"] = analyse
                st.rerun()

    analyse = st.session_state.get("ki_upload_analyse", {})

    technik_default = analyse.get("technik", "")
    beschreibung_default = analyse.get("beschreibung", "")
    schlagworte_default = analyse.get("schlagworte", "")

    stile_default = filter_optionen(
        text_zu_liste(analyse.get("stile", "")),
        STIL_OPTIONEN,
    )

    techniken_default = filter_optionen(
        text_zu_liste(analyse.get("techniken", "")),
        TECHNIK_OPTIONEN,
    )

    gattungen_default = filter_optionen(
        text_zu_liste(analyse.get("gattungen", "")),
        GATTUNG_OPTIONEN,
    )

    stile_neu = st.multiselect(
        "Stil / Epoche",
        STIL_OPTIONEN,
        default=stile_default,
    )

    techniken_neu = st.multiselect(
        "Techniken",
        TECHNIK_OPTIONEN,
        default=techniken_default,
    )

    gattungen_neu = st.multiselect(
        "Gattung / Motiv",
        GATTUNG_OPTIONEN,
        default=gattungen_default,
    )

    technik_neu = st.text_input(
        "Technik",
        value=technik_default,
    )

    masse_neu = st.text_input("Maße")
    standort_neu = st.text_input("Standort")
    rechte_neu = st.text_input("Rechte")

    beschreibung_neu = st.text_area(
        "Beschreibung",
        value=beschreibung_default,
    )

    schlagworte_neu = st.text_input(
        "Schlagworte",
        value=schlagworte_default,
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

                werk_titel = titel_neu if titel_neu else uploaded_file.name

                daten = {
                    "dateiname": eindeutiger_name,
                    "kuenstler": kuenstler_neu,
                    "titel": werk_titel,
                    "jahr": jahr_neu,
                    "technik": technik_neu,
                    "masse": masse_neu,
                    "standort": standort_neu,
                    "rechte": rechte_neu,
                    "owner_email": user_email,
                    "deleted_at": None,
                    "deleted_by": None,
                    "beschreibung": beschreibung_neu,
                    "schlagworte": schlagworte_neu,
                    "bildpfad": public_url,
                    "thumbnailpfad": thumbnail_url,
                    "stile": liste_zu_text(stile_neu),
                    "techniken": liste_zu_text(techniken_neu),
                    "gattungen": liste_zu_text(gattungen_neu),
                }

                datensatz_speichern(daten)

                log_activity(
                    user_email=user_email,
                    action="upload",
                    artwork_title=werk_titel,
                    details=f"Datei hochgeladen: {uploaded_file.name}",
                )

                gespeichert += 1

            st.session_state["ki_upload_analyse"] = {}

            st.success(f"{gespeichert} Bilder gespeichert.")
            st.session_state["seite"] = "Archiv durchsuchen"
            st.session_state["ansicht"] = "Galerieansicht"
            st.rerun()