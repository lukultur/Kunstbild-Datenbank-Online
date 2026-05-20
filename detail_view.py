import requests
import streamlit as st

from permissions import can_manage_artwork
from trash import soft_delete_werk


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
    soft_delete_werk(
        row,
        user_email,
        "Detailansicht",
    )


def detail_bild_anzeigen(bild_url):
    st.image(
        bild_url,
        use_container_width=True,
    )