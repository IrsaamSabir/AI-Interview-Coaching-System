import re


def clean_text(text: str) -> str:
    """
    Light cleaning only - preserve characters that are part of tech skill names.
    Keeps:  letters, digits, spaces, hyphen (-), dot (.), slash (/), hash (#), plus (+)
    Strips: everything else (commas, brackets, @, !, etc.)
    """
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s\-\.\/\#\+]', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()