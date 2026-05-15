import streamlit as st
from supabase import create_client


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase_admin = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


ROLLEN = [
    "nutzer",
    "redakteur",
    "admin",
]


def rollen_laden():
    try:
        response = (
            supabase_admin.table("user_roles")
            .select("*")
            .order("email")
            .execute()
        )

        return response.data or []

    except Exception as error:
        st.error(f"Rollen konnten nicht geladen werden: {error}")
        return []


def rolle_speichern(email, rolle):
    try:
        vorhandene = (
            supabase_admin.table("user_roles")
            .select("*")
            .eq("email", email)
            .execute()
        )

        if vorhandene.data:
            (
                supabase_admin.table("user_roles")
                .update({"role": rolle})
                .eq("email", email)
                .execute()
            )

        else:
            (
                supabase_admin.table("user_roles")
                .insert(
                    {
                        "email": email,
                        "role": rolle,
                    }
                )
                .execute()
            )

        return True, "Rolle wurde gespeichert."

    except Exception as error:
        return False, f"Rolle konnte nicht gespeichert werden: {error}"


def rolle_loeschen(email):
    try:
        (
            supabase_admin.table("user_roles")
            .delete()
            .eq("email", email)
            .execute()
        )

        return True, "Rolle wurde entfernt. Der Nutzer ist danach automatisch wieder Nutzer."

    except Exception as error:
        return False, f"Rolle konnte nicht entfernt werden: {error}"


def admin_benutzerverwaltung():
    st.header("Benutzerverwaltung")

    st.caption(
        "Hier werden Sonderrollen verwaltet. Nutzer ohne Eintrag in dieser Tabelle haben automatisch die Rolle „nutzer“."
    )

    st.subheader("Neue Rolle vergeben oder bestehende ändern")

    with st.form("rolle_formular"):
        email = st.text_input("E-Mail-Adresse")

        rolle = st.selectbox(
            "Rolle",
            ROLLEN,
            index=0,
        )

        speichern = st.form_submit_button("Rolle speichern")

    if speichern:
        if not email.strip():
            st.error("Bitte eine E-Mail-Adresse eingeben.")

        else:
            success, message = rolle_speichern(
                email.strip().lower(),
                rolle,
            )

            if success:
                st.success(message)
                st.rerun()

            else:
                st.error(message)

    st.divider()

    st.subheader("Aktuelle Sonderrollen")

    rollen = rollen_laden()

    if not rollen:
        st.info("Noch keine Sonderrollen vorhanden.")
        return

    for eintrag in rollen:
        email = eintrag.get("email", "")
        rolle = eintrag.get("role", "")

        col1, col2, col3 = st.columns([3, 1, 1])

        with col1:
            st.write(f"**{email}**")

        with col2:
            st.write(rolle)

        with col3:
            if st.button(
                "Entfernen",
                key=f"rolle_entfernen_{email}",
            ):
                success, message = rolle_loeschen(email)

                if success:
                    st.success(message)
                    st.rerun()

                else:
                    st.error(message)