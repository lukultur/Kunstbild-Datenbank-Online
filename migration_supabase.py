import sqlite3
import uuid
import mimetypes
from pathlib import Path

import requests

SUPABASE_URL = "https://jxnvqhmupyrmyrvbkogp.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imp4bnZxaG11cHlybXlydmJrb2dwIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Nzg2MjgzNTksImV4cCI6MjA5NDIwNDM1OX0._bmLQLhZesgGK2A8ghJbWM-HoCHgH5NXYm0Q6HvYR8U"
SUPABASE_BUCKET = "kunstbilder"

DB_FILE = "kunstbilder.db"
BILDER_ORDNER = Path("Bilder")


def upload_to_supabase(local_file: Path):
    suffix = local_file.suffix
    neuer_name = f"{uuid.uuid4()}{suffix}"

    mime_type, _ = mimetypes.guess_type(local_file)
    if mime_type is None:
        mime_type = "application/octet-stream"

    upload_url = (
        f"{SUPABASE_URL}/storage/v1/object/"
        f"{SUPABASE_BUCKET}/{neuer_name}"
    )

    headers = {
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "apikey": SUPABASE_KEY,
        "Content-Type": mime_type,
        "x-upsert": "false",
    }

    with open(local_file, "rb") as f:
        response = requests.post(
            upload_url,
            headers=headers,
            data=f
        )

    if response.status_code not in (200, 201):
        raise RuntimeError(
            f"Upload fehlgeschlagen: {response.status_code} - {response.text}"
        )

    public_url = (
        f"{SUPABASE_URL}/storage/v1/object/public/"
        f"{SUPABASE_BUCKET}/{neuer_name}"
    )

    return neuer_name, public_url


conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

cursor.execute(
    """
    SELECT rowid, Dateiname, Bildpfad
    FROM kunstbilder
    """
)

daten = cursor.fetchall()

print(f"{len(daten)} Datensätze gefunden.")

migriert = 0
uebersprungen = 0
fehlend = 0

for rowid, dateiname, bildpfad in daten:
    if str(bildpfad).startswith("http"):
        print(f"Übersprungen, bereits online: {dateiname}")
        uebersprungen += 1
        continue

    lokaler_pfad = BILDER_ORDNER / str(dateiname)

    if not lokaler_pfad.exists():
        print(f"DATEI FEHLT: {lokaler_pfad}")
        fehlend += 1
        continue

    try:
        neuer_name, public_url = upload_to_supabase(lokaler_pfad)

        cursor.execute(
            """
            UPDATE kunstbilder
            SET Dateiname = ?,
                Bildpfad = ?
            WHERE rowid = ?
            """,
            (
                neuer_name,
                public_url,
                rowid,
            ),
        )

        conn.commit()

        print(f"Migriert: {dateiname} -> {neuer_name}")
        migriert += 1

    except Exception as e:
        print(f"FEHLER bei {dateiname}: {e}")

conn.close()

print("")
print("Migration abgeschlossen.")
print(f"Migriert: {migriert}")
print(f"Übersprungen: {uebersprungen}")
print(f"Fehlende Dateien: {fehlend}")