# backend/app/utils/helpers.py
import re

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_valid_syntax(email: str) -> bool:
    if not email or "@" not in email:
        return False
    return bool(EMAIL_REGEX.match(email))
