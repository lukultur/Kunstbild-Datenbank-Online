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


def komplette_kunstbilder_laden():
    try:
        response = (
            supabase_backup.table("kunstbilder")
            .select("*")
            .execute()
        )

        return response.data or []

    except Exception as error:
        st.error(f"Kunstbilder konnten nicht geladen werden: {error}")
        return []


def backup_excel_erzeugen():
    daten = komplette_kunstbilder_laden()

    if not daten:
        return None

    df = pd.DataFrame(daten)

    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="kunstbilder_backup",
        )

    output.seek(0)

    return output.getvalue()