from io import BytesIO
from pathlib import Path
import uuid

from PIL import Image
from supabase import create_client
import streamlit as st


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
SUPABASE_BUCKET = st.secrets["SUPABASE_BUCKET"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


def thumbnail_erzeugen(uploaded_file):

    bild = Image.open(
        BytesIO(uploaded_file.getvalue())
    )

    bild.thumbnail((600, 600))

    buffer = BytesIO()

    bild.save(
        buffer,
        format="JPEG",
        quality=75,
        optimize=True,
    )

    buffer.seek(0)

    return buffer.getvalue()


def bild_nach_supabase(uploaded_file):

    suffix = Path(uploaded_file.name).suffix

    eindeutiger_name = f"{uuid.uuid4()}{suffix}"
    thumbnail_name = f"thumb_{uuid.uuid4()}.jpg"

    file_bytes = uploaded_file.getvalue()
    thumbnail_bytes = thumbnail_erzeugen(uploaded_file)

    supabase.storage.from_(SUPABASE_BUCKET).upload(
        eindeutiger_name,
        file_bytes,
        {
            "content-type": uploaded_file.type
        },
    )

    supabase.storage.from_(SUPABASE_BUCKET).upload(
        thumbnail_name,
        thumbnail_bytes,
        {
            "content-type": "image/jpeg"
        },
    )

    public_url = (
        supabase.storage.from_(
            SUPABASE_BUCKET
        ).get_public_url(
            eindeutiger_name
        )
    )

    thumbnail_url = (
        supabase.storage.from_(
            SUPABASE_BUCKET
        ).get_public_url(
            thumbnail_name
        )
    )

    return (
        eindeutiger_name,
        public_url,
        thumbnail_url,
    )


def bild_html(url):

    return f"""
    <div class="fixed-image-box">
        <img src="{url}">
    </div>
    """