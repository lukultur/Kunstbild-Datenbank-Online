import io

import pandas as pd
import streamlit as st
from supabase import create_client


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase_backup = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


def tabelle_laden(tabellenname):
    try:
        response = (
            supabase_backup.table(tabellenname)
            .select("*")
            .execute()
        )

        return response.data or []

    except Exception as error:
        st.error(f"Tabelle {tabellenname} konnte nicht geladen werden: {error}")
        return []


def backup_excel_erzeugen():
    kunstbilder = tabelle_laden("kunstbilder")
    activity_log = tabelle_laden("activity_log")
    user_roles = tabelle_laden("user_roles")

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        pd.DataFrame(kunstbilder).to_excel(
            writer,
            index=False,
            sheet_name="kunstbilder_backup",
        )

        pd.DataFrame(activity_log).to_excel(
            writer,
            index=False,
            sheet_name="activity_log_backup",
        )

        pd.DataFrame(user_roles).to_excel(
            writer,
            index=False,
            sheet_name="user_roles_backup",
        )

    output.seek(0)

    return output.getvalue()