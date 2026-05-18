import requests
import streamlit as st
from datetime import datetime, timezone

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

from admin import admin_benutzerverwaltung
from logging_utils import log_activity


st.set_page_config(
    page_title="Kunstbild-Datenbank",
    layout="wide",
)

lade_css()


if not is_logged_in():
    login_view()
    st.stop()


def text_zu_liste(text):
    if not text:
        return []
    return [x.strip() for x in str(text).split(",") if x.strip()]


def liste_zu_text(liste):
    return ", ".join(liste)


def kurzer_titel(text, max_laenge=32):
    text = str(text)
    if len(text) > max_laenge:
        return text[:max_laenge] + "..."
    return text


def filter_optionen(werte, optionen):
    return [wert for wert in werte if wert in optionen]


def darf_werk_verwalten(row, rolle, user_email):
    if rolle == "admin":
        return True

    if rolle == "redakteur":
        return str(row.get("owner_email", "")).lower() == str(user_email).lower()

    return False


def soft_delete_werk(row, user_email, quelle):
    deleted_at = datetime.now(timezone.utc).isoformat()

    datensatz_aktualisieren(
        row["id"],
        {
            "deleted_at": deleted_at,
            "deleted_by": user_email,
        },
    )

    log_activity(
        user_email=user_email,
        action="soft_delete",
        artwork_id=int(row["id"]),
        artwork_title=str(row.get("titel", "")),
        details=f"Datensatz per Soft Delete aus {quelle} ausgeblendet.",
    )


rolle = get_current_role().lower()
user_email = get_current_email()

darf_admin = rolle == "admin"
darf_upload = rolle in ["admin", "redakteur"]


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


if st.session_state["seite"] == "Benutzerverwaltung" and darf_admin:

    admin_benutzerverwaltung()


elif st.session_state["seite"] == "Neues Bild hinzufügen" and darf_upload:

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


else:

    df = daten_laden()
    st.write(df[["deleted_at"]].head(20))

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
                kann_verwalten = darf_werk_verwalten(row, rolle, user_email)

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
                                    bild_download = requests.get(
                                        row["bildpfad"],
                                        timeout=20,
                                    ).content

                                    st.download_button(
                                        label="⬇ Bild herunterladen",
                                        data=bild_download,
                                        file_name=str(row["dateiname"]),
                                        mime="application/octet-stream",
                                        key=f"download_{row['id']}",
                                        use_container_width=True,
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
                                        soft_delete_werk(
                                            row=row,
                                            user_email=user_email,
                                            quelle="Galerie",
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
            kann_verwalten = darf_werk_verwalten(row, rolle, user_email)

            if st.button("← Zurück zur Galerie"):
                st.session_state["ansicht"] = "Galerieansicht"
                st.session_state["ausgewaehlte_id"] = None
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