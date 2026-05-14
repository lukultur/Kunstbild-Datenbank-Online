from io import BytesIO

import pandas as pd
from supabase import create_client
import streamlit as st


SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


def daten_laden():

    response = (
        supabase.table("kunstbilder")
        .select("*")
        .order("titel")
        .execute()
    )

    df = pd.DataFrame(response.data)

    if df.empty:

        df = pd.DataFrame(
            columns=[
                "id",
                "dateiname",
                "kuenstler",
                "titel",
                "jahr",
                "technik",
                "masse",
                "standort",
                "rechte",
                "beschreibung",
                "schlagworte",
                "bildpfad",
                "thumbnailpfad",
                "stile",
                "techniken",
                "gattungen",
            ]
        )

    for spalte in [
        "thumbnailpfad",
        "stile",
        "techniken",
        "gattungen",
    ]:

        if spalte not in df.columns:
            df[spalte] = ""

    return df.fillna("")


def datensatz_speichern(daten):

    supabase.table("kunstbilder").insert(daten).execute()


def datensatz_aktualisieren(datensatz_id, daten):

    (
        supabase.table("kunstbilder")
        .update(daten)
        .eq("id", datensatz_id)
        .execute()
    )


def datensatz_loeschen(
    datensatz_id,
    dateiname,
    thumbnailpfad="",
):

    try:
        supabase.storage.from_("kunstbilder").remove(
            [str(dateiname)]
        )

    except Exception:
        pass

    try:

        if thumbnailpfad:

            thumb_name = str(thumbnailpfad).split("/")[-1]

            supabase.storage.from_("kunstbilder").remove(
                [thumb_name]
            )

    except Exception:
        pass

    (
        supabase.table("kunstbilder")
        .delete()
        .eq("id", datensatz_id)
        .execute()
    )


def excel_export_erzeugen(df):

    export_df = df.drop(
        columns=["id"],
        errors="ignore",
    )

    output = BytesIO()

    with pd.ExcelWriter(
        output,
        engine="openpyxl",
    ) as writer:

        export_df.to_excel(
            writer,
            index=False,
            sheet_name="Kunstbilder",
        )

    output.seek(0)

    return output