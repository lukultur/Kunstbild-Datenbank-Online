from io import BytesIO

import requests
from PIL import Image

from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Image as RLImage,
    PageBreak,
)


def pdf_katalog_erzeugen(df):
    output = BytesIO()

    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        rightMargin=1.8 * cm,
        leftMargin=1.8 * cm,
        topMargin=1.8 * cm,
        bottomMargin=1.8 * cm,
    )

    styles = getSampleStyleSheet()

    titel_style = ParagraphStyle(
        "KatalogTitel",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        alignment=TA_LEFT,
        spaceAfter=18,
    )

    werk_titel_style = ParagraphStyle(
        "WerkTitel",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
        spaceBefore=8,
        spaceAfter=6,
    )

    meta_style = ParagraphStyle(
        "Meta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        spaceAfter=4,
    )

    text_style = ParagraphStyle(
        "Beschreibung",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10,
        leading=14,
        spaceBefore=6,
        spaceAfter=10,
    )

    story = []

    story.append(Paragraph("Kunstbild-Datenbank – Werkverzeichnis", titel_style))
    story.append(Paragraph(f"Ausgewählte Werke: {len(df)}", meta_style))
    story.append(Spacer(1, 0.5 * cm))

    for index, row in df.iterrows():
        titel = str(row.get("titel", "") or "Ohne Titel")
        kuenstler = str(row.get("kuenstler", "") or "")
        jahr = str(row.get("jahr", "") or "")
        technik = str(row.get("technik", "") or "")
        masse = str(row.get("masse", "") or "")
        stile = str(row.get("stile", "") or "")
        techniken = str(row.get("techniken", "") or "")
        gattungen = str(row.get("gattungen", "") or "")
        beschreibung = str(row.get("beschreibung", "") or "")
        schlagworte = str(row.get("schlagworte", "") or "")
        bild_url = str(row.get("thumbnailpfad", "") or row.get("bildpfad", ""))

        story.append(Paragraph(titel, werk_titel_style))

        if bild_url:
            try:
                response = requests.get(bild_url, timeout=20)
                image_bytes = BytesIO(response.content)

                pil_img = Image.open(image_bytes)
                width, height = pil_img.size

                max_width = 14 * cm
                max_height = 9 * cm

                ratio = min(max_width / width, max_height / height)
                img_width = width * ratio
                img_height = height * ratio

                image_bytes.seek(0)

                story.append(
                    RLImage(
                        image_bytes,
                        width=img_width,
                        height=img_height,
                    )
                )

                story.append(Spacer(1, 0.25 * cm))

            except Exception:
                story.append(Paragraph("[Bild konnte nicht geladen werden]", meta_style))

        if kuenstler:
            story.append(Paragraph(f"<b>Künstler:</b> {kuenstler}", meta_style))

        if jahr:
            story.append(Paragraph(f"<b>Jahr:</b> {jahr}", meta_style))

        if technik:
            story.append(Paragraph(f"<b>Technik:</b> {technik}", meta_style))

        if masse:
            story.append(Paragraph(f"<b>Maße:</b> {masse}", meta_style))

        if stile:
            story.append(Paragraph(f"<b>Stil / Epoche:</b> {stile}", meta_style))

        if techniken:
            story.append(Paragraph(f"<b>Techniken:</b> {techniken}", meta_style))

        if gattungen:
            story.append(Paragraph(f"<b>Gattung / Motiv:</b> {gattungen}", meta_style))

        if beschreibung:
            story.append(Paragraph(f"<b>Beschreibung:</b><br/>{beschreibung}", text_style))

        if schlagworte:
            story.append(Paragraph(f"<b>Schlagworte:</b> {schlagworte}", meta_style))

        if index < len(df) - 1:
            story.append(PageBreak())

    doc.build(story)
    output.seek(0)

    return output