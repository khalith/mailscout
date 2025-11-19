# worker/verifier/syntax_engine.py
import re

# RFC-light regex (practical)
EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def is_syntax_valid(addr: str) -> bool:
    if not addr or "@" not in addr:
        return False
    return EMAIL_REGEX.match(addr) is not None

def normalize_email(addr: str) -> str:
    if not addr:
        return ""
    return addr.strip().lower()
