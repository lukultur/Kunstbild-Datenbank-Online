from datetime import datetime, timezone

import streamlit as st
from supabase import create_client

from database import datensatz_aktualisieren
from activity import log_activity


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase_trash = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


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


def werk_wiederherstellen(werk, user_email):
    try:
        datensatz_aktualisieren(
            werk["id"],
            {
                "deleted_at": None,
                "deleted_by": None,
            },
        )

        log_activity(
            user_email=user_email,
            action="restore",
            artwork_id=int(werk["id"]),
            artwork_title=str(werk.get("titel", "")),
            details="Datensatz aus dem Papierkorb wiederhergestellt.",
        )

        return True, "Werk wurde wiederhergestellt."

    except Exception as error:
        return False, f"Werk konnte nicht wiederhergestellt werden: {error}"

def geloeschte_werke_laden(rolle, user_email):
    try:
        query = (
            supabase_trash.table("kunstbilder")
            .select("*")
            .not_.is_("deleted_at", "null")
            .order("deleted_at", desc=True)
        )

        if rolle == "redakteur":
            query = query.eq("owner_email", user_email)

        response = query.execute()
        return response.data or []

    except Exception as error:
        st.error(f"Gelöschte Werke konnten nicht geladen werden: {error}")
        return []