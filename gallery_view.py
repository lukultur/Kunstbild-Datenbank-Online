import requests
import streamlit as st

from storage import bild_html
from trash import soft_delete_werk
from activity import log_activity
from permissions import can_manage_artwork
from filter_utils import kurzer_titel


def bild_download_laden(bildpfad):
    try:
        return requests.get(
            bildpfad,
            timeout=20,
        ).content

    except Exception:
        return None

def bild_download_button(
    row,
    bild_download,
):
    st.download_button(
        label="⬇ Bild herunterladen",
        data=bild_download,
        file_name=str(row["dateiname"]),
        mime="application/octet-stream",
        key=f"download_{row['id']}",
        use_container_width=True,
    )

def bild_karte_titel(row):
    titel = kurzer_titel(row.get("titel", ""))

    if not titel:
        titel = "Ohne Titel"

    return titel
def darf_bearbeiten(
    row,
    rolle,
    user_email,
):
    return can_manage_artwork(
        row,
        rolle,
        user_email,
    )
def bild_loeschen(
    row,
    user_email,
):
    soft_delete_werk(
        row,
        user_email,
        "Galerieansicht",
    )
def bild_anzeigen(bild_url):
    st.markdown(
        bild_html(bild_url),
        unsafe_allow_html=True,
    )
    
def bild_meta_block(row):
    kuenstler = str(row.get("kuenstler", "") or "").strip()
    jahr = str(row.get("jahr", "") or "").strip()

    if kuenstler.lower() in ["empty", "none", "nan", "nat"]:
        kuenstler = ""

    if jahr.lower() in ["empty", "none", "nan", "nat"]:
        jahr = ""

    st.markdown(
        f"""
        <div class="kunst-title">
            {bild_karte_titel(row)}
        </div>
        <div class="kunst-meta-kompakt">
            <strong>{kuenstler}</strong><br>
            {jahr}
        </div>
        """,
        unsafe_allow_html=True,
    )