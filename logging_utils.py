import streamlit as st
from supabase import create_client


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase_logging = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


def log_activity(
    user_email,
    action,
    artwork_id=None,
    artwork_title="",
    details="",
):
    print("LOGGING WIRD AUSGEFÜHRT")

    try:
        (
            supabase_logging.table("activity_log")
            .insert(
                {
                    "user_email": user_email,
                    "action": action,
                    "artwork_id": artwork_id,
                    "artwork_title": artwork_title,
                    "details": details,
                }
            )
            .execute()
        )

    except Exception as error:
    st.error(f"Logging-Fehler: {error}")