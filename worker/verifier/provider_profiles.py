# worker/verifier/provider_profiles.py
from typing import Optional

COMMON_PROVIDERS = {
    "gmail.com": "gmail",
    "googlemail.com": "gmail",
    "yahoo.com": "yahoo",
    "hotmail.com": "microsoft",
    "outlook.com": "microsoft",
    "icloud.com": "apple",
    "protonmail.com": "protonmail",
    "zoho.com": "zoho",
}

def identify_provider(domain: str) -> Optional[str]:
    if not domain:
        return None
    d = domain.lower()
    return COMMON_PROVIDERS.get(d)
