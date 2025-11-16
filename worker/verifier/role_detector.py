# worker/verifier/role_detector.py

ROLE_PREFIXES = {
    "admin", "contact", "support", "info", "hr", "sales",
    "billing", "service", "helpdesk", "postmaster"
}

def is_role_email(email: str) -> bool:
    local = email.split("@")[0].lower()
    return local in ROLE_PREFIXES
