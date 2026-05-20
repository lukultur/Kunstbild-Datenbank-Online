import requests
import streamlit as st

from gallery_view import bild_loeschen
from storage import bild_html
from trash import soft_delete_werk
from permissions import can_manage_artwork
from filter_utils import kurzer_titel
from activity import log_activity

def detail_bild_download_laden(bildpfad):
    try:
        return requests.get(
            bildpfad,
            timeout=20,
        ).content

    except Exception:
        return None

def detail_download_button(
    row,
    bild_download,
):
    st.download_button(
        label="Bild herunterladen",
        data=bild_download,
        file_name=str(row["dateiname"]),
        mime="application/octet-stream",
        key=f"detail_download_{row['id']}",
        use_container_width=True,
    )

def detail_darf_bearbeiten(
    row,
    rolle,
    user_email,
):
    return can_manage_artwork(
        row,
        rolle,
        user_email,
    )

def detail_download_button(
    row,
    bild_download,
):
    detail_download_button(
    row,
    bild_download,
)

def detail_meta_block(row):
    st.markdown(
        f"""
        ### {row.get("titel", "")}

        **Künstler:** {row.get("kuenstler", "")}  
        **Jahr:** {row.get("jahr", "")}  
        **Technik:** {row.get("technik", "")}  
        **Maße:** {row.get("masse", "")}  
        **Standort:** {row.get("standort", "")}  
        **Rechte:** {row.get("rechte", "")}  
        **Besitzer:** {row.get("owner_email", "")}  
        **Stil / Epoche:** {row.get("stile", "")}  
        **Techniken:** {row.get("techniken", "")}  
        **Gattung / Motiv:** {row.get("gattungen", "")}  
        **Beschreibung:** {row.get("beschreibung", "")}  
        **Schlagworte:** {row.get("schlagworte", "")}
        """
    )

def detail_bild_loeschen(
    row,
    user_email,
):
    detail_bild_loeschen(
    row,
    user_email,
)