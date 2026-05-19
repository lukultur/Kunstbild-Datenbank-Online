def text_zu_liste(text):
    if not text:
        return []
    return [x.strip() for x in str(text).split(",") if x.strip()]


def liste_zu_text(liste):
    return ", ".join(liste)


def kurzer_titel(text, max_laenge=32):
    text = str(text)
    if len(text) > max_laenge:
        return text[:max_laenge] + "..."
    return text


def filter_optionen(werte, optionen):
    return [wert for wert in werte if wert in optionen]