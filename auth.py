import streamlit as st
from supabase import create_client


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase_auth = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


def init_auth_state():
    if "auth_user" not in st.session_state:
        st.session_state["auth_user"] = None

    if "auth_email" not in st.session_state:
        st.session_state["auth_email"] = ""

    if "auth_role" not in st.session_state:
        st.session_state["auth_role"] = "nutzer"

    if "auth_session" not in st.session_state:
        st.session_state["auth_session"] = None


def is_logged_in():
    init_auth_state()
    return st.session_state["auth_user"] is not None


def get_current_email():
    init_auth_state()
    return st.session_state.get("auth_email", "")


def get_current_role():
    init_auth_state()
    return st.session_state.get("auth_role", "nutzer")


def has_role(*roles):
    return get_current_role() in roles


def lade_rolle(email):
    try:
        role_response = (
            supabase_auth.table("user_roles")
            .select("role")
            .eq("email", email)
            .execute()
        )

        if role_response.data:
            return role_response.data[0].get("role", "nutzer")

        return "nutzer"

    except Exception:
        return "nutzer"


def login(email, password):
    try:
        response = supabase_auth.auth.sign_in_with_password(
            {
                "email": email.strip(),
                "password": password,
            }
        )

        user = response.user
        session = response.session

        if not user:
            return False, "Login fehlgeschlagen."

        rolle = lade_rolle(user.email)

        st.session_state["auth_user"] = user
        st.session_state["auth_email"] = user.email
        st.session_state["auth_session"] = session
        st.session_state["auth_role"] = rolle

        return True, "Login erfolgreich."

    except Exception as error:
        return False, f"Login fehlgeschlagen: {error}"


def logout():
    try:
        supabase_auth.auth.sign_out()
    except Exception:
        pass

    st.session_state["auth_user"] = None
    st.session_state["auth_email"] = ""
    st.session_state["auth_role"] = "nutzer"
    st.session_state["auth_session"] = None


def register(email, password):
    try:
        response = supabase_auth.auth.sign_up(
            {
                "email": email.strip(),
                "password": password.strip(),
            }
        )

        if response.user:
            return True, "Registrierung erfolgreich. Bitte bestätige deine E-Mail-Adresse."

        return False, "Registrierung konnte nicht abgeschlossen werden."

    except Exception as error:
        return False, f"Registrierung fehlgeschlagen: {error}"


def reset_password(email):
    try:
        supabase_auth.auth.reset_password_email(email.strip())
        return True, "E-Mail zum Zurücksetzen des Passworts wurde versendet."

    except Exception as error:
        return False, f"Passwort-Reset fehlgeschlagen: {error}"


def login_view():
    init_auth_state()

    st.title("Kunstbild-Datenbank")
    st.subheader("Anmeldung")

    tab_login, tab_register, tab_reset = st.tabs(
        [
            "Login",
            "Registrieren",
            "Passwort vergessen",
        ]
    )

    with tab_login:
        email = st.text_input(
            "E-Mail-Adresse",
            key="login_email",
        )

        password = st.text_input(
            "Passwort",
            type="password",
            key="login_password",
        )

        if st.button("Einloggen"):
            success, message = login(email, password)

            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)

    with tab_register:
        register_email = st.text_input(
            "E-Mail-Adresse",
            key="register_email",
        )

        register_password = st.text_input(
            "Passwort",
            type="password",
            key="register_password",
        )

        register_password_repeat = st.text_input(
            "Passwort wiederholen",
            type="password",
            key="register_password_repeat",
        )

        if st.button("Registrieren"):
            if register_password.strip() != register_password_repeat.strip():
                st.error("Die Passwörter stimmen nicht überein.")

            elif len(register_password.strip()) < 8:
                st.error("Das Passwort muss mindestens 8 Zeichen lang sein.")

            else:
                success, message = register(
                    register_email,
                    register_password,
                )

                if success:
                    st.success(message)
                else:
                    st.error(message)

    with tab_reset:
        reset_email = st.text_input(
            "E-Mail-Adresse",
            key="reset_email",
        )

        if st.button("Passwort zurücksetzen"):
            success, message = reset_password(reset_email)

            if success:
                st.success(message)
            else:
                st.error(message)