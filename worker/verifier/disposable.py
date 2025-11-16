# worker/verifier/disposable.py

DISPOSABLE_DOMAINS = {
    "mailinator.com",
    "tempmail.com",
    "10minutemail.com",
    "trashmail.com",
    "yopmail.com"
}

def is_disposable(domain: str) -> bool:
    return domain.lower() in DISPOSABLE_DOMAINS
