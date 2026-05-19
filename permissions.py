def normalize_role(role):
    return str(role or "nutzer").strip().lower()


def is_admin(role):
    return normalize_role(role) == "admin"


def can_upload(role):
    return normalize_role(role) in ["admin", "redakteur"]


def can_manage_artwork(row, role, user_email):
    role = normalize_role(role)

    if role == "admin":
        return True

    if role == "redakteur":
        return (
            str(row.get("owner_email", "")).strip().lower()
            == str(user_email).strip().lower()
        )

    return False