import streamlit as st
from supabase import create_client


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase_activity = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


def log_activity(
    user_email,
    action,
    artwork_id=None,
    artwork_title=None,
    details=None,
):
    try:
        supabase_activity.table("activity_log").insert(
            {
                "user_email": user_email,
                "action": action,
                "artwork_id": artwork_id,
                "artwork_title": artwork_title,
                "details": details,
            }
        ).execute()

    except Exception as error:
        st.warning(f"Logging-Fehler: {error}")


def aktivitaeten_laden():
    try:
        response = (
            supabase_activity.table("activity_log")
            .select("*")
            .order("created_at", desc=True)
            .limit(300)
            .execute()
        )

        return response.data or []

    except Exception as error:
        st.error(f"Aktivitäten konnten nicht geladen werden: {error}")
        return []
def log_download(user_email, row):
    log_activity(
        user_email=user_email,
        action="download",
        artwork_id=int(row["id"]),
        artwork_title=str(row.get("titel", "")),
        details=f"Download von {row.get('dateiname', '')}",
    )