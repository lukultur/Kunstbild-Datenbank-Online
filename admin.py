import pandas as pd
import streamlit as st
from supabase import create_client

from trash import geloeschte_werke_laden, werk_wiederherstellen


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
                .insert({"email": email, "role": rolle})
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


def aktivitaeten_laden():
    try:
        response = (
            supabase_admin.table("activity_log")
            .select("*")
            .order("created_at", desc=True)
            .limit(300)
            .execute()
        )
        return response.data or []

    except Exception as error:
        st.error(f"Aktivitäten konnten nicht geladen werden: {error}")
        return []


def papierkorb_ansicht(rolle, user_email):
    st.subheader("Papierkorb")

    if rolle == "admin":
        st.caption("Admin sieht alle gelöschten Werke.")
    else:
        st.caption("Redakteure sehen nur eigene gelöschte Werke.")

    werke = geloeschte_werke_laden(rolle, user_email)

    if not werke:
        st.info("Keine gelöschten Werke vorhanden.")
        return

    for werk in werke:
        titel = werk.get("titel", "")
        kuenstler = werk.get("kuenstler", "")
        owner = werk.get("owner_email", "")
        deleted_by = werk.get("deleted_by", "")
        deleted_at = werk.get("deleted_at", "")

        with st.container(border=True):
            st.write(f"**{titel}**")
            st.write(f"Künstler: {kuenstler}")
            st.write(f"Besitzer: {owner}")
            st.write(f"Gelöscht von: {deleted_by}")
            st.write(f"Gelöscht am: {deleted_at}")

            if st.button(
                "Wiederherstellen",
                key=f"restore_{werk['id']}",
                use_container_width=True,
            ):
                success, message = werk_wiederherstellen(
                    werk,
                    user_email,
                )

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)


def admin_benutzerverwaltung(rolle="admin", user_email=""):
    st.header("Administration")

    if rolle == "admin":
        tab_rollen, tab_log, tab_papierkorb = st.tabs(
            [
                "Benutzerrollen",
                "Aktivitätsprotokoll",
                "Papierkorb",
            ]
        )
    else:
        tab_papierkorb = st.tabs(["Papierkorb"])[0]

    if rolle == "admin":
        with tab_rollen:
            st.subheader("Benutzerrollen")

            st.caption(
                "Hier werden Sonderrollen verwaltet. Nutzer ohne Eintrag haben automatisch die Rolle „nutzer“."
            )

            with st.form("rolle_formular"):
                email = st.text_input("E-Mail-Adresse")

                rolle_neu = st.selectbox(
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
                        rolle_neu.strip().lower(),
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
            else:
                for eintrag in rollen:
                    email = eintrag.get("email", "")
                    rolle_eintrag = eintrag.get("role", "")

                    col1, col2, col3 = st.columns([3, 1, 1])

                    with col1:
                        st.write(f"**{email}**")

                    with col2:
                        st.write(rolle_eintrag)

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

        with tab_log:
            st.subheader("Aktivitätsprotokoll")

            st.caption("Die letzten 300 protokollierten Aktionen im System.")

            aktivitaeten = aktivitaeten_laden()

            if not aktivitaeten:
                st.info("Noch keine Aktivitäten vorhanden.")
            else:
                df = pd.DataFrame(aktivitaeten)

                if "created_at" in df.columns:
                    df["created_at"] = pd.to_datetime(
                        df["created_at"],
                        errors="coerce",
                    )

                nutzer_filter = "Alle"
                aktion_filter = "Alle"

                col_filter1, col_filter2 = st.columns([1, 1])

                with col_filter1:
                    if "user_email" in df.columns:
                        nutzer = sorted(
                            df["user_email"]
                            .fillna("")
                            .astype(str)
                            .unique()
                            .tolist()
                        )

                        nutzer_filter = st.selectbox(
                            "Nutzer filtern",
                            ["Alle"] + nutzer,
                        )

                with col_filter2:
                    if "action" in df.columns:
                        aktionen = sorted(
                            df["action"]
                            .fillna("")
                            .astype(str)
                            .unique()
                            .tolist()
                        )

                        aktion_filter = st.selectbox(
                            "Aktion filtern",
                            ["Alle"] + aktionen,
                        )

                gefiltert = df.copy()

                if nutzer_filter != "Alle" and "user_email" in gefiltert.columns:
                    gefiltert = gefiltert[
                        gefiltert["user_email"].astype(str) == nutzer_filter
                    ]

                if aktion_filter != "Alle" and "action" in gefiltert.columns:
                    gefiltert = gefiltert[
                        gefiltert["action"].astype(str) == aktion_filter
                    ]

                spalten = [
                    "created_at",
                    "user_email",
                    "action",
                    "artwork_title",
                    "artwork_id",
                    "details",
                ]

                vorhandene_spalten = [
                    spalte for spalte in spalten if spalte in gefiltert.columns
                ]

                st.dataframe(
                    gefiltert[vorhandene_spalten],
                    use_container_width=True,
                    hide_index=True,
                )

        with tab_papierkorb:
            papierkorb_ansicht(rolle, user_email)

    else:
        with tab_papierkorb:
            papierkorb_ansicht(rolle, user_email)