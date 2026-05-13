from PIL import Image
import streamlit as st
import pandas as pd
import uuid
import requests
from pathlib import Path
from io import BytesIO
from supabase import create_client

PASSWORT = "kunstarchiv2026"

STIL_OPTIONEN = [
    "Renaissance", "Barock", "Klassizismus", "Romantik", "Realismus",
    "Impressionismus", "Expressionismus", "Kubismus", "Fauvismus",
    "Surrealismus", "Abstrakte Kunst", "Pop Art", "Fotorealismus",
    "Neue Sachlichkeit", "Verismus", "Symbolismus", "Jugendstil",
    "Dadaismus", "Konstruktivismus", "Minimalismus", "Konzeptkunst",
    "Informel", "Tachismus", "Arte Povera", "Op Art", "Land Art",
    "Street Art", "Zeitgenössische Kunst",
]

TECHNIK_OPTIONEN = [
    "Ölmalerei", "Acrylmalerei", "Aquarellmalerei", "Pastellmalerei",
    "Gouache", "Tempera", "Mischtechnik", "Collage", "Tusche",
    "Zeichnung", "Kohle", "Radierung", "Lithografie", "Siebdruck",
    "Fotografie", "Digitale Kunst",
]

GATTUNG_OPTIONEN = [
    "Porträt", "Selbstporträt", "Landschaft", "Stadtansicht",
    "Stillleben", "Akt", "Interieur", "Tierdarstellung",
    "Historienbild", "Religiöses Motiv", "Abstrakt", "Architektur",
    "Naturdarstellung", "Gesellschaftsszene",
]

st.set_page_config(page_title="Kunstbild-Datenbank", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_BUCKET = st.secrets["SUPABASE_BUCKET"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

st.markdown(
    """
    <style>
    .fixed-image-box {
        width: 100%;
        height: 260px;
        display: flex;
        align-items: center;
        justify-content: center;
        background: #f7f7f7;
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 0.75rem;
    }

    .fixed-image-box img {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
    }

    .kunst-title {
        height: 3.1em;
        overflow: hidden;
        font-size: 1.15rem;
        font-weight: 700;
        line-height: 1.25;
        margin-bottom: 0.35rem;
    }

    .kunst-meta {
        min-height: 5.2em;
        font-size: 0.95rem;
    }

    .stButton > button {
        width: 100%;
    }

    .stDownloadButton > button {
        width: 100%;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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
st.caption("Recherche, Vorschau, Upload, Export und Verwaltung deiner Kunstbilder")


def text_zu_liste(text):
    if not text:
        return []
    return [x.strip() for x in str(text).split(",") if x.strip()]


def liste_zu_text(liste):
    return ", ".join(liste)


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
                "id", "dateiname", "kuenstler", "titel", "jahr", "technik",
                "masse", "standort", "rechte", "beschreibung", "schlagworte",
                "bildpfad", "thumbnailpfad", "stile", "techniken", "gattungen",
            ]
        )

    for spalte in ["thumbnailpfad", "stile", "techniken", "gattungen"]:
        if spalte not in df.columns:
            df[spalte] = ""

    return df.fillna("")


def datensatz_speichern(daten):
    supabase.table("kunstbilder").insert(daten).execute()


def datensatz_aktualisieren(datensatz_id, daten):
    supabase.table("kunstbilder").update(daten).eq("id", datensatz_id).execute()


def datensatz_loeschen(datensatz_id, dateiname, thumbnailpfad=""):
    try:
        supabase.storage.from_(SUPABASE_BUCKET).remove([str(dateiname)])
    except Exception:
        pass

    try:
        if thumbnailpfad:
            thumb_name = str(thumbnailpfad).split("/")[-1]
            supabase.storage.from_(SUPABASE_BUCKET).remove([thumb_name])
    except Exception:
        pass

    supabase.table("kunstbilder").delete().eq("id", datensatz_id).execute()


def thumbnail_erzeugen(uploaded_file):
    bild = Image.open(BytesIO(uploaded_file.getvalue()))
    bild.thumbnail((600, 600))

    buffer = BytesIO()
    bild.save(buffer, format="JPEG", quality=75, optimize=True)
    buffer.seek(0)

    return buffer.getvalue()


def bild_nach_supabase(uploaded_file):
    suffix = Path(uploaded_file.name).suffix
    eindeutiger_name = f"{uuid.uuid4()}{suffix}"
    thumbnail_name = f"thumb_{uuid.uuid4()}.jpg"

    file_bytes = uploaded_file.getvalue()
    thumbnail_bytes = thumbnail_erzeugen(uploaded_file)

    supabase.storage.from_(SUPABASE_BUCKET).upload(
        eindeutiger_name,
        file_bytes,
        {"content-type": uploaded_file.type},
    )

    supabase.storage.from_(SUPABASE_BUCKET).upload(
        thumbnail_name,
        thumbnail_bytes,
        {"content-type": "image/jpeg"},
    )

    public_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(eindeutiger_name)
    thumbnail_url = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(thumbnail_name)

    return eindeutiger_name, public_url, thumbnail_url


def kurzer_titel(text, max_laenge=32):
    text = str(text)
    if len(text) > max_laenge:
        return text[:max_laenge] + "..."
    return text


def bild_html(url):
    return f"""
    <div class="fixed-image-box">
        <img src="{url}">
    </div>
    """


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
            gespeichert = 0

            for uploaded_file in uploaded_files:
                eindeutiger_name, public_url, thumbnail_url = bild_nach_supabase(uploaded_file)

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
                    "thumbnailpfad": thumbnail_url,
                    "stile": liste_zu_text(stile_neu),
                    "techniken": liste_zu_text(techniken_neu),
                    "gattungen": liste_zu_text(gattungen_neu),
                }

                datensatz_speichern(daten)
                gespeichert += 1

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

    kuenstler_filter = st.sidebar.selectbox("Künstler", kuenstler_liste)

    stil_filter = st.sidebar.multiselect("Stil / Epoche", STIL_OPTIONEN)
    technik_filter = st.sidebar.multiselect("Techniken", TECHNIK_OPTIONEN)
    gattung_filter = st.sidebar.multiselect("Gattung / Motiv", GATTUNG_OPTIONEN)

    gefiltert = df.copy()

    if suchbegriff:
        suchbegriff = suchbegriff.lower()
        gefiltert = gefiltert[
            gefiltert.astype(str)
            .apply(lambda row: row.str.lower().str.contains(suchbegriff).any(), axis=1)
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

                bild_url = row["thumbnailpfad"] if row["thumbnailpfad"] else row["bildpfad"]

                with spalten[i]:
                    with st.container(border=True):
                        st.markdown(
                            bild_html(bild_url),
                            unsafe_allow_html=True,
                        )

                        if st.button("Groß anzeigen", key=f"gross_{row['id']}"):
                            st.session_state["ausgewaehlte_id"] = int(row["id"])
                            st.session_state["ansicht"] = "Detailansicht"
                            st.rerun()

                        try:
                            bild_download = requests.get(row["bildpfad"], timeout=20).content

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
                                    row.get("thumbnailpfad", ""),
                                )

                                st.success("Datensatz wurde gelöscht.")
                                st.rerun()

                        st.markdown(
                            f'<div class="kunst-title">{kurzer_titel(row.get("titel", ""))}</div>',
                            unsafe_allow_html=True,
                        )

                        st.markdown(
                            f"""
                            <div class="kunst-meta">
                            <strong>{row.get("kuenstler", "") or "&nbsp;"}</strong><br>
                            {row.get("jahr", "") or "&nbsp;"}<br>
                            Stil: {row.get("stile", "") or "—"}<br>
                            Gattung: {row.get("gattungen", "") or "—"}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )

    else:
        if len(gefiltert) == 0:
            st.info("Keine Einträge gefunden.")
        else:
            auswahl_liste = [
                f"{row.get('kuenstler', '')} – {row.get('titel', '')} [{row.get('id', '')}]"
                for _, row in gefiltert.iterrows()
            ]

            vorauswahl_index = 0

            if st.session_state["ausgewaehlte_id"] is not None:
                for idx, row_check in gefiltert.iterrows():
                    if int(row_check["id"]) == int(st.session_state["ausgewaehlte_id"]):
                        vorauswahl_index = idx
                        break

            auswahl = st.selectbox("Werk auswählen", auswahl_liste, index=vorauswahl_index)
            index = auswahl_liste.index(auswahl)
            row = gefiltert.iloc[index]

            if st.button("Zurück zur Galerie"):
                st.session_state["ansicht"] = "Galerieansicht"
                st.rerun()

            col1, col2 = st.columns([1.4, 1])

            with col1:
                st.image(row["bildpfad"], use_container_width=True)

                try:
                    bild_download = requests.get(row["bildpfad"], timeout=20).content

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
                        bearb_kuenstler = st.text_input("Künstler", value=str(row.get("kuenstler", "")))
                        bearb_titel = st.text_input("Titel", value=str(row.get("titel", "")))
                        bearb_jahr = st.text_input("Jahr", value=str(row.get("jahr", "")))
                        bearb_technik = st.text_input("Technik", value=str(row.get("technik", "")))
                        bearb_masse = st.text_input("Maße", value=str(row.get("masse", "")))
                        bearb_standort = st.text_input("Standort", value=str(row.get("standort", "")))
                        bearb_rechte = st.text_input("Rechte", value=str(row.get("rechte", "")))

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
                            "stile": liste_zu_text(bearb_stile),
                            "techniken": liste_zu_text(bearb_techniken),
                            "gattungen": liste_zu_text(bearb_gattungen),
                        }

                        datensatz_aktualisieren(row["id"], neue_daten)
                        st.success("Änderungen wurden gespeichert.")
                        st.rerun()

                st.divider()

                with st.popover("🗑️ Datensatz löschen"):
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
                        st.rerun()