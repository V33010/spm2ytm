import re


def clean_string(text: str) -> str:
    """Remove non-alphanumeric, special chars, non-ASCII."""
    text = re.sub(r"[^a-zA-Z0-9\s]", " ", text)
    return "".join(char if ord(char) < 128 else " " for char in text).strip()


def save_list_to_file(lines: list[str], file_path: str):
    with open(file_path, "w", encoding="utf-8") as f:
        for line in lines:
            f.write(line + "\n")
