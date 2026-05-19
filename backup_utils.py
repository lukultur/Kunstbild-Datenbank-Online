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


def vollstaendige_rollenliste_erzeugen(kunstbilder, activity_log, user_roles):
    rollen_map = {}

    for eintrag in user_roles:
        email = str(eintrag.get("email", "")).strip().lower()
        rolle = str(eintrag.get("role", "nutzer")).strip().lower()

        if email:
            rollen_map[email] = rolle

    emails = set(rollen_map.keys())

    for werk in kunstbilder:
        owner_email = str(werk.get("owner_email", "")).strip().lower()
        deleted_by = str(werk.get("deleted_by", "")).strip().lower()

        if owner_email:
            emails.add(owner_email)

        if deleted_by:
            emails.add(deleted_by)

    for aktivitaet in activity_log:
        user_email = str(aktivitaet.get("user_email", "")).strip().lower()

        if user_email:
            emails.add(user_email)

    vollstaendige_liste = []

    for email in sorted(emails):
        vollstaendige_liste.append(
            {
                "email": email,
                "role": rollen_map.get(email, "nutzer"),
            }
        )

    return vollstaendige_liste


def backup_excel_erzeugen():
    kunstbilder = tabelle_laden("kunstbilder")
    activity_log = tabelle_laden("activity_log")
    user_roles = tabelle_laden("user_roles")

    vollstaendige_user_roles = vollstaendige_rollenliste_erzeugen(
        kunstbilder,
        activity_log,
        user_roles,
    )

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

        pd.DataFrame(vollstaendige_user_roles).to_excel(
            writer,
            index=False,
            sheet_name="user_roles_backup",
        )

    output.seek(0)

    return output.getvalue()