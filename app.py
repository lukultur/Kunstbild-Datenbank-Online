import requests
import streamlit as st

from constants import (
    STIL_OPTIONEN,
    TECHNIK_OPTIONEN,
    GATTUNG_OPTIONEN,
)

from styles import lade_css

from database import (
    daten_laden,
    datensatz_speichern,
    datensatz_aktualisieren,
    excel_export_erzeugen,
)

from storage import (
    bild_nach_supabase,
    bild_html,
)

from pdf_export import pdf_katalog_erzeugen
from ai_tools import ki_upload_analyse

from auth import (
    login_view,
    is_logged_in,
    logout,
    get_current_email,
    get_current_role,
)

from admin import admin_benutzerverwaltung, papierkorb_ansicht
from activity import log_activity

from filter_utils import (
    text_zu_liste,
    liste_zu_text,
    kurzer_titel,
    filter_optionen,
)

from upload_view import upload_view
from gallery_view import (
    bild_karte_titel,
    darf_bearbeiten,
    bild_loeschen,
    bild_download_button,
    bild_download_laden,
    bild_anzeigen,
    bild_meta_block,
)

from permissions import (
    normalize_role,
    is_admin,
    can_upload,
    can_manage_artwork,
)

from trash import soft_delete_werk

st.set_page_config(
    page_title="Kunstbild-Datenbank",
    layout="wide",
)

lade_css()


if not is_logged_in():
    login_view()
    st.stop()




rolle = normalize_role(get_current_role())
user_email = get_current_email()

darf_admin = is_admin(rolle)
darf_upload = can_upload(rolle)


if "seite" not in st.session_state:
    st.session_state["seite"] = "Archiv durchsuchen"

if "ansicht" not in st.session_state:
    st.session_state["ansicht"] = "Galerieansicht"

if "ausgewaehlte_id" not in st.session_state:
    st.session_state["ausgewaehlte_id"] = None

if "ki_upload_analyse" not in st.session_state:
    st.session_state["ki_upload_analyse"] = {}


st.title("Kunstbild-Datenbank")
st.caption("Recherche, Vorschau, Upload, Export und Verwaltung deiner Kunstbilder")


with st.sidebar:
    st.header("Navigation")

    st.caption(f"Angemeldet als: {user_email}")
    st.caption(f"Rolle: {rolle}")

    bereiche = ["Archiv durchsuchen"]

    if darf_upload:
        bereiche.append("Neues Bild hinzufügen")

    if rolle in ["admin", "redakteur"]:
        bereiche.append("Papierkorb")    

    if darf_admin:
        bereiche.append("Benutzerverwaltung")

    if st.session_state["seite"] not in bereiche:
        st.session_state["seite"] = "Archiv durchsuchen"

    seite = st.radio(
        "Bereich wählen",
        bereiche,
        index=bereiche.index(st.session_state["seite"]),
    )

    st.session_state["seite"] = seite

    st.divider()

    if st.button("Abmelden"):
        logout()
        st.rerun()

if st.session_state["seite"] == "Papierkorb" and rolle in ["admin", "redakteur"]:

    papierkorb_ansicht(
        rolle=rolle,
        user_email=user_email,
    )


elif st.session_state["seite"] == "Benutzerverwaltung" and darf_admin:

    admin_benutzerverwaltung(
        rolle=rolle,
        user_email=user_email,
    )


elif st.session_state["seite"] == "Neues Bild hinzufügen" and darf_upload:

    upload_view(user_email)


else:

    df = daten_laden()
    
    if "deleted_at" in df.columns:
        df = df[
            df["deleted_at"].isna()
            | (df["deleted_at"].astype(str).str.strip() == "")
            | (df["deleted_at"].astype(str).str.lower() == "none")
            | (df["deleted_at"].astype(str).str.lower() == "nan")
            | (df["deleted_at"].astype(str).str.lower() == "nat")
    ]

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

        for start in range(0, len(gefiltert), 3):
            spalten = st.columns(3)

            for i in range(3):
                if start + i >= len(gefiltert):
                    continue

                row = gefiltert.iloc[start + i]

                kann_verwalten = darf_bearbeiten(
                    row,
                    rolle,
                    user_email,
                )

                bild_url = (
                    row["thumbnailpfad"]
                    if row["thumbnailpfad"]
                    else row["bildpfad"]
                )

                with spalten[i]:
                    with st.container(border=True):

                        bild_anzeigen(bild_url)

                        bild_meta_block(row)

                    aktion1, aktion2 = st.columns([1, 1], gap="small")

                    with aktion1:
                        if st.button(
                            "⛶",
                            key=f"gross_{row['id']}",
                            help="Detailansicht öffnen",
                            use_container_width=True,
                        ):
                            st.session_state["ausgewaehlte_id"] = int(row["id"])
                            st.session_state["ansicht"] = "Detailansicht"
                            st.rerun()

                    with aktion2:
                        with st.popover("⋯", use_container_width=True):
                            try:
                                bild_download = bild_download_laden(
                                    row["bildpfad"]
                                )

                                bild_download_button(
                                    row,
                                    bild_download,
                                )

                            except Exception:
                                st.info("Download aktuell nicht verfügbar.")

                            if kann_verwalten:
                                st.divider()

                                if st.button(
                                    "🗑 Datensatz löschen",
                                    key=f"confirm_delete_gallery_{row['id']}",
                                    use_container_width=True,
                                ):
                                    bild_loeschen(
                                        row,
                                        user_email,
                                    )

                                    st.success("Datensatz wurde gelöscht.")
                                    st.rerun()

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
            kann_verwalten = can_manage_artwork(
                                          row,
                                          rolle,
                                          user_email,
)

            if st.button("← Zurück zur Galerie"):
                st.session_state["ansicht"] = "Galerieansicht"
                st.session_state["ausgewaehlte_id"] = None
                st.rerun()

            col1, col2 = st.columns([1.4, 1])

            with col1:
                st.image(row["bildpfad"], use_container_width=True)

                try:
                    bild_download = bild_download_laden(
                                                                row["bildpfad"]
)

                    st.download_button(
                        label="Bild herunterladen",
                        data=bild_download,
                        file_name=str(row["dateiname"]),
                        mime="application/octet-stream",
                        key=f"detail_download_{row['id']}",
                        use_container_width=True,
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
                st.write(f"**Besitzer:** {row.get('owner_email', '')}")
                st.write(f"**Stil / Epoche:** {row.get('stile', '')}")
                st.write(f"**Techniken:** {row.get('techniken', '')}")
                st.write(f"**Gattung / Motiv:** {row.get('gattungen', '')}")
                st.write(f"**Beschreibung:** {row.get('beschreibung', '')}")
                st.write(f"**Schlagworte:** {row.get('schlagworte', '')}")

                if darf_admin:
                    st.divider()

                    with st.expander("Besitzer ändern"):
                        neuer_besitzer = st.text_input(
                            "Neue Besitzer-E-Mail",
                            value=str(row.get("owner_email", "")),
                            key=f"owner_email_{row['id']}",
                        )

                        if st.button(
                            "Besitzer speichern",
                            key=f"owner_save_{row['id']}",
                            use_container_width=True,
                        ):
                            alter_besitzer = str(row.get("owner_email", ""))

                            datensatz_aktualisieren(
                                row["id"],
                                {
                                    "owner_email": neuer_besitzer.strip().lower(),
                                },
                            )

                            log_activity(
                                user_email=user_email,
                                action="owner_change",
                                artwork_id=int(row["id"]),
                                artwork_title=str(row.get("titel", "")),
                                details=(
                                    f"Besitzer geändert von "
                                    f"{alter_besitzer} zu {neuer_besitzer.strip().lower()}."
                                ),
                            )

                            st.success("Besitzer wurde geändert.")
                            st.rerun()

                if kann_verwalten:
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

                            log_activity(
                                user_email=user_email,
                                action="edit",
                                artwork_id=int(row["id"]),
                                artwork_title=str(bearb_titel),
                                details="Datensatz bearbeitet.",
                            )

                            st.success("Änderungen wurden gespeichert.")
                            st.rerun()

                if kann_verwalten:
                    st.divider()

                    with st.popover("🗑 Datensatz löschen"):
                        st.warning("Diesen Datensatz wirklich ausblenden?")

                        if st.button(
                            "Ja, Datensatz ausblenden",
                            key=f"confirm_delete_detail_{row['id']}",
                        ):
                            soft_delete_werk(
                                row=row,
                                user_email=user_email,
                                quelle="Detailansicht",
                            )

                            st.success("Datensatz wurde gelöscht.")
                            st.session_state["ansicht"] = "Galerieansicht"
                            st.session_state["ausgewaehlte_id"] = None
                            st.rerun()