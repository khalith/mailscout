# worker/verifier/disposable.py
# Minimal disposable provider list (extendable dynamic list recommended)
DISPOSABLE_PROVIDERS = {
    "mailinator.com", "10minutemail.com", "tempmail.com", "trashmail.com",
    "guerrillamail.com", "yopmail.com", "dispostable.com",
}

def is_disposable(domain: str) -> bool:
    if not domain:
        return False
    return domain.lower() in DISPOSABLE_PROVIDERS
